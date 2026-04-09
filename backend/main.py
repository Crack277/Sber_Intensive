from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

# Импортируем функцию предсказания
from neiro import predict_client_risk

app = FastAPI(
    title="СберКот Risk API",
    description="API для оценки кредитного риска клиентов",
    version="1.0.0"
)

# Настройка CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модель данных клиента
class ClientData(BaseModel):
    monthly_payment: float = Field(..., description="Ежемесячный платеж")
    monthly_income: float = Field(..., description="Ежемесячный доход")
    total_expenses: float = Field(..., description="Общие расходы")
    tenure_months: int = Field(..., description="Срок обслуживания (мес)")
    total_overdue_days: int = Field(0, description="Дни просрочки")

    # Дополнительные поля
    age: Optional[int] = None
    credit_score: Optional[int] = None
    num_loans: Optional[int] = 0
    employment_years: Optional[float] = None
    num_past_delinquencies: Optional[int] = 0
    has_bankruptcy: Optional[int] = 0
    dti_ratio: Optional[float] = 0.0
    payment_to_income_ratio: Optional[float] = 0.0
    loan_rate: Optional[float] = 15.0
    num_credit_contracts: Optional[int] = 1
    num_closed_loans: Optional[int] = 0
    max_overdue_days: Optional[int] = 0
    requested_amount: Optional[float] = 0.0
    approved_amount: Optional[float] = 0.0
    children_count: Optional[int] = 0
    living_area_sqm: Optional[float] = 50.0
    work_experience_total_years: Optional[int] = 5
    has_higher_education: Optional[int] = 0
    is_salary_client: Optional[int] = 0
    has_credit_card: Optional[int] = 0
    uses_mobile_banking: Optional[int] = 0
    marital_status: Optional[str] = "холост"
    income_source: Optional[str] = "зарплата"
    employment_type: Optional[str] = "частный сектор"
    position_level: Optional[str] = "специалист"
    loan_purpose: Optional[str] = "потребительский"
    client_segment: Optional[str] = "массовый"


class PredictionResponse(BaseModel):
    risk_level: str = Field(..., description="Уровень риска")
    confidence: float = Field(..., description="Уверенность модели")
    risk_description: str = Field(..., description="Описание риска")


RISK_DESCRIPTIONS = {
    "forgot": "🟢 Низкий риск - клиент мог забыть о платеже. Рекомендуется напоминание.",
    "worried": "🟡 Средний риск - клиент испытывает временные трудности. Рекомендуется реструктуризация.",
    "bankruptcy": "🔴 Высокий риск - возможное банкротство. Требуется немедленное вмешательство."
}


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "СберКот Risk API",
        "version": "1.0.0",
        "endpoints": ["/predict", "/health"]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "СберКот"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_risk(client: ClientData):
    try:
        client_dict = client.model_dump(exclude_none=True)
        risk_label, confidence = predict_client_risk(client_dict)

        return PredictionResponse(
            risk_level=risk_label,
            confidence=round(float(confidence), 4),
            risk_description=RISK_DESCRIPTIONS.get(risk_label, "Неизвестный уровень риска")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)