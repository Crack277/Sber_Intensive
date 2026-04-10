from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / 'risk_model.pkl'


class RiskPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.model_path = Path(model_path)

        if self.model_path.exists():
            self.load_model(self.model_path)
        else:
            raise FileNotFoundError(f'Модель не найдена: {self.model_path}')

    def load_model(self, path: Path):
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.label_encoder = data['label_encoder']
        self.feature_columns = data['feature_columns']

    @staticmethod
    def _heuristic_risk_score(client_data: dict) -> float:
        monthly_income = float(client_data.get('monthly_income', 0) or 0)
        total_expenses = float(client_data.get('total_expenses', 0) or 0)
        monthly_payment = float(client_data.get('monthly_payment', 0) or 0)
        total_overdue_days = float(client_data.get('total_overdue_days', 0) or 0)
        max_overdue_days = float(client_data.get('max_overdue_days', 0) or 0)
        num_past_delinquencies = float(client_data.get('num_past_delinquencies', 0) or 0)
        has_bankruptcy = float(client_data.get('has_bankruptcy', 0) or 0)
        dti_ratio = float(client_data.get('dti_ratio', 0) or 0)
        payment_to_income_ratio = float(client_data.get('payment_to_income_ratio', 0) or 0)
        num_credit_contracts = float(client_data.get('num_credit_contracts', 0) or 0)
        num_closed_loans = float(client_data.get('num_closed_loans', 0) or 0)
        is_salary_client = float(client_data.get('is_salary_client', 0) or 0)
        has_autopayment = float(client_data.get('has_autopayment', 0) or 0)

        expense_to_income = total_expenses / (monthly_income + 1)
        debt_to_income = monthly_payment / (monthly_income + 1)
        free_cashflow_ratio = (monthly_income - total_expenses - monthly_payment) / (monthly_income + 1)
        overdue_factor = min(total_overdue_days / 90, 1.0)
        max_overdue_factor = min(max_overdue_days / 60, 1.0)
        delinquency_factor = min(num_past_delinquencies / 5, 1.0)
        contract_pressure = min(num_credit_contracts / (num_closed_loans + 1), 2.5) / 2.5

        score = (
            0.30 * min(max(dti_ratio, debt_to_income), 1.2)
            + 0.24 * min(payment_to_income_ratio, 1.0)
            + 0.20 * overdue_factor
            + 0.12 * max_overdue_factor
            + 0.08 * delinquency_factor
            + 0.06 * contract_pressure
            + 0.14 * has_bankruptcy
            + 0.06 * min(expense_to_income, 1.0)
            + 0.12 * max(-free_cashflow_ratio, 0.0)
            - 0.03 * is_salary_client
            - 0.02 * has_autopayment
        )

        if total_overdue_days >= 45:
            score = max(score, 0.82)
        if total_overdue_days >= 75 or max_overdue_days >= 45:
            score = max(score, 0.92)
        if payment_to_income_ratio >= 0.55 and total_overdue_days >= 30:
            score = max(score, 0.88)

        return float(np.clip(score, 0.0, 1.0))

    @classmethod
    def _apply_risk_overrides(cls, client_data: dict, predicted_label: str) -> str:
        total_overdue_days = float(client_data.get('total_overdue_days', 0) or 0)
        max_overdue_days = float(client_data.get('max_overdue_days', 0) or 0)
        payment_to_income_ratio = float(client_data.get('payment_to_income_ratio', 0) or 0)
        monthly_income = float(client_data.get('monthly_income', 0) or 0)
        monthly_payment = float(client_data.get('monthly_payment', 0) or 0)
        total_expenses = float(client_data.get('total_expenses', 0) or 0)
        debt_to_income = monthly_payment / (monthly_income + 1)
        free_cashflow_ratio = (monthly_income - total_expenses - monthly_payment) / (monthly_income + 1)

        if (
            total_overdue_days == 0
            and max_overdue_days == 0
            and max(payment_to_income_ratio, debt_to_income) <= 0.20
            and free_cashflow_ratio >= 0.22
        ):
            return 'forgot'
        if total_overdue_days >= 75 or max_overdue_days >= 45:
            return 'bankruptcy'
        if total_overdue_days >= 45 and max(payment_to_income_ratio, debt_to_income) >= 0.35:
            return 'bankruptcy'
        if total_overdue_days >= 20 or max(payment_to_income_ratio, debt_to_income) >= 0.40:
            return 'worried' if predicted_label == 'forgot' else predicted_label
        return predicted_label

    @classmethod
    def _normalize_confidence(cls, probabilities, class_idx: int, client_data: dict, risk_label: str) -> float:
        top_probability = float(probabilities[class_idx])
        sorted_probabilities = np.sort(np.asarray(probabilities, dtype=float))[::-1]
        second_probability = float(sorted_probabilities[1]) if len(sorted_probabilities) > 1 else 0.0
        margin = max(0.0, top_probability - second_probability)
        entropy = -float(np.sum(np.asarray(probabilities, dtype=float) * np.log(np.asarray(probabilities, dtype=float) + 1e-12)))
        normalized_entropy = entropy / np.log(len(probabilities))
        model_certainty = np.clip(0.55 * top_probability + 0.45 * margin, 0.0, 1.0)

        heuristic_score = cls._heuristic_risk_score(client_data)
        class_centers = {
            'forgot': 0.14,
            'worried': 0.48,
            'bankruptcy': 0.88,
        }
        center = class_centers.get(risk_label, 0.5)
        archetype_fit = 1.0 - min(abs(heuristic_score - center) / 0.34, 1.0)
        ambiguity_penalty = normalized_entropy * 0.12

        normalized = 0.52 + 0.22 * model_certainty + 0.18 * archetype_fit - ambiguity_penalty
        return float(np.clip(normalized, 0.58, 0.93))

    def predict(self, client_data):
        client_df = pd.DataFrame([client_data])

        for col in self.feature_columns:
            if col not in client_df.columns:
                client_df[col] = 0

        monthly_payment = client_data.get('monthly_payment', 0)
        monthly_income = client_data.get('monthly_income', 1)
        total_expenses = client_data.get('total_expenses', 1)
        tenure_months = client_data.get('tenure_months', 1)
        total_overdue_days = client_data.get('total_overdue_days', 0)
        approved_amount = client_data.get('approved_amount', 0)
        requested_amount = client_data.get('requested_amount', 0)
        num_credit_contracts = client_data.get('num_credit_contracts', 0)
        num_closed_loans = client_data.get('num_closed_loans', 0)
        max_overdue_days = client_data.get('max_overdue_days', 0)

        client_df['debt_to_income'] = monthly_payment / (monthly_income + 1)
        client_df['overdue_ratio'] = total_overdue_days / (tenure_months + 1)
        client_df['loan_success_rate'] = approved_amount / (requested_amount + 1)
        client_df['credit_utilization'] = num_credit_contracts / (num_closed_loans + 1)
        client_df['payment_burden'] = monthly_payment / (total_expenses + 1)
        client_df['expense_to_income'] = total_expenses / (monthly_income + 1)
        client_df['overdue_severity'] = max_overdue_days / (total_overdue_days + 1)

        features = client_df[self.feature_columns].fillna(0)
        scaled_features = self.scaler.transform(features)

        prediction = self.model.predict(scaled_features)[0]
        probabilities = self.model.predict_proba(scaled_features)[0]
        initial_risk_label = self.label_encoder.inverse_transform([prediction])[0]
        risk_label = self._apply_risk_overrides(client_data, initial_risk_label)
        class_idx = list(self.label_encoder.classes_).index(initial_risk_label)
        confidence = self._normalize_confidence(probabilities, class_idx, client_data, risk_label)

        return risk_label, confidence


_predictor = RiskPredictor()


def predict_client_risk(client_data: dict) -> tuple[str, float]:
    return _predictor.predict(client_data)
