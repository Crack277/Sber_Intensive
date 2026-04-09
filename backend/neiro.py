import pandas as pd
import numpy as np
import joblib
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder


class RiskPredictor:
    def __init__(self, model_path='risk_model.pkl'):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.model_path = model_path

        # Загружаем уже обученную модель
        if os.path.exists(model_path):
            self.load_model(model_path)
        else:
            print("❌ Модель не найдена! Запустите обучение сначала.")
            raise FileNotFoundError(f"Модель {model_path} не найдена")

    def load_model(self, path):
        """Загружает модель"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.label_encoder = data['label_encoder']
        self.feature_columns = data['feature_columns']
        print(f"✅ Модель загружена из {path}")
        print(f"📊 Доступные классы: {list(self.label_encoder.classes_)}")

    def predict(self, client_data):
        """Предсказывает риск для клиента"""
        # Создаем DataFrame
        client_df = pd.DataFrame([client_data])

        # Добавляем недостающие колонки
        for col in self.feature_columns:
            if col not in client_df.columns:
                client_df[col] = 0

        # Создаем дополнительные признаки
        monthly_payment = client_data.get('monthly_payment', 0)
        monthly_income = client_data.get('monthly_income', 1)
        total_expenses = client_data.get('total_expenses', 1)
        tenure_months = client_data.get('tenure_months', 1)
        total_overdue_days = client_data.get('total_overdue_days', 0)

        client_df['debt_to_income'] = monthly_payment / (monthly_income + 1)
        client_df['overdue_ratio'] = total_overdue_days / (tenure_months + 1)
        client_df['payment_burden'] = monthly_payment / (total_expenses + 1)

        # Выбираем нужные колонки
        X = client_df[self.feature_columns].fillna(0)

        # Нормализуем
        X_scaled = self.scaler.transform(X)

        # Предсказываем
        pred = self.model.predict(X_scaled)[0]
        proba = self.model.predict_proba(X_scaled)[0]

        risk_label = self.label_encoder.inverse_transform([pred])[0]

        # Получаем вероятность
        class_idx = list(self.label_encoder.classes_).index(risk_label)
        confidence = proba[class_idx]

        return risk_label, confidence


# Создаем глобальный экземпляр (загружается 1 раз при импорте)
print("🔄 Загрузка модели предсказания риска...")
_predictor = RiskPredictor('risk_model.pkl')


def predict_client_risk(client_data: dict) -> tuple:
    """
    Предсказывает риск для клиента

    Parameters:
    client_data: dict с данными клиента

    Returns:
    tuple: (risk_label, confidence)
    risk_label: 'forgot', 'worried', или 'bankruptcy'
    confidence: float от 0 до 1
    """
    return _predictor.predict(client_data)