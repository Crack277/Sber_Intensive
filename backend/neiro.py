from pathlib import Path

import joblib
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

        client_df['debt_to_income'] = monthly_payment / (monthly_income + 1)
        client_df['overdue_ratio'] = total_overdue_days / (tenure_months + 1)
        client_df['payment_burden'] = monthly_payment / (total_expenses + 1)

        features = client_df[self.feature_columns].fillna(0)
        scaled_features = self.scaler.transform(features)

        prediction = self.model.predict(scaled_features)[0]
        probabilities = self.model.predict_proba(scaled_features)[0]
        risk_label = self.label_encoder.inverse_transform([prediction])[0]
        class_idx = list(self.label_encoder.classes_).index(risk_label)
        confidence = probabilities[class_idx]

        return risk_label, confidence


_predictor = RiskPredictor()


def predict_client_risk(client_data: dict) -> tuple[str, float]:
    return _predictor.predict(client_data)
