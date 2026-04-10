import csv
import random
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

if __package__:
    from risk_predictor import predict_client_risk
else:
    from risk_predictor import predict_client_risk

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / 'bank_clients_filtered.csv'

FIRST_NAMES = ['Иван', 'Анна', 'Дмитрий', 'Елена', 'Максим', 'Ольга', 'Алексей', 'Мария']
LAST_NAMES = ['Иванов', 'Смирнова', 'Петров', 'Кузнецова', 'Соколов', 'Попова', 'Волков', 'Орлова']

RISK_DESCRIPTIONS = {
    'forgot': 'Низкий риск: клиент мог просто забыть о платеже. Рекомендуется напоминание.',
    'worried': 'Средний риск: клиент испытывает временные сложности. Рекомендуется реструктуризация.',
    'bankruptcy': 'Высокий риск: возможен тяжёлый дефолт. Требуется быстрое сопровождение.',
}

ASSISTANT_RECOMMENDATIONS = {
    'forgot': [
        'Напомнить о платеже за 3 и за 1 день до даты списания.',
        'Предложить автоплатёж или перенос даты списания под день зарплаты.',
        'Сохранить мягкий сценарий коммуникации без давления и штрафного тона.',
    ],
    'worried': [
        'Проверить кредитные каникулы или частичную реструктуризацию.',
        'Снизить ежемесячную нагрузку через новый график платежей.',
        'Подключить менеджера с персональным планом удержания клиента.',
    ],
    'bankruptcy': [
        'Передать кейс в приоритетную обработку сопровождения.',
        'Собрать подтверждение дохода и актуальной долговой нагрузки.',
        'Предложить антикризисный план: пауза, реструктуризация или снижение платежа.',
    ],
}

RETENTION_QUICK_REPLIES = {
    'worried': [
        'У меня временно просел доход',
        'Можно уменьшить платёж на несколько месяцев?',
        'Боюсь выйти в просрочку',
    ],
    'bankruptcy': [
        'Сейчас не хватает денег даже на минимальный платёж',
        'Нужна срочная реструктуризация',
        'Хочу обсудить перенос платежей и заморозку штрафов',
    ],
}


def _to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_str(value: str, default: str = '') -> str:
    if value is None:
        return default
    cleaned = str(value).strip()
    return cleaned or default


class ClientData(BaseModel):
    monthly_payment: float = Field(..., description='Ежемесячный платёж')
    monthly_income: float = Field(..., description='Ежемесячный доход')
    total_expenses: float = Field(..., description='Общие расходы')
    tenure_months: int = Field(..., description='Срок обслуживания, месяцев')
    total_overdue_days: int = Field(0, description='Дни просрочки')
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
    marital_status: Optional[str] = 'холост'
    income_source: Optional[str] = 'зарплата'
    employment_type: Optional[str] = 'частный сектор'
    position_level: Optional[str] = 'специалист'
    loan_purpose: Optional[str] = 'потребительский'
    client_segment: Optional[str] = 'массовый'


class PredictionResponse(BaseModel):
    risk_level: str = Field(..., description='Уровень риска')
    confidence: float = Field(..., description='Уверенность модели')
    risk_description: str = Field(..., description='Описание риска')


class ClientProfileResponse(BaseModel):
    client_id: str
    full_name: str
    data: ClientData
    risk: PredictionResponse
    assistant_recommendations: list[str]
    retention_dialog_enabled: bool
    retention_summary: str
    retention_quick_replies: list[str]


class RetentionChatRequest(BaseModel):
    client_id: str
    client_name: str
    risk_level: str
    message: str


class RetentionChatResponse(BaseModel):
    reply: str
    next_steps: list[str]


app = FastAPI(
    title='Sber Risk API',
    description='API для оценки кредитного риска клиента и удерживающего сопровождения',
    version='1.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _dataset_rows() -> list[dict[str, str]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f'Не найден датасет клиентов: {DATASET_PATH}')

    with DATASET_PATH.open('r', encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file))


DATASET_ROWS = _dataset_rows()


def _build_client_name(index: int) -> str:
    first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
    last_name = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
    return f'{first_name} {last_name}'


def _row_to_client_data(row: dict[str, str]) -> ClientData:
    return ClientData(
        monthly_payment=_to_float(row.get('monthly_payment')),
        monthly_income=_to_float(row.get('monthly_income')),
        total_expenses=_to_float(row.get('total_expenses')),
        tenure_months=_to_int(row.get('tenure_months'), 1),
        total_overdue_days=_to_int(row.get('total_overdue_days')),
        age=_to_int(row.get('age'), None) if row.get('age') else None,
        credit_score=_to_int(row.get('credit_score'), None) if row.get('credit_score') else None,
        num_loans=_to_int(row.get('num_credit_contracts')),
        employment_years=_to_float(row.get('work_experience_total_years')),
        num_past_delinquencies=_to_int(row.get('num_past_delinquencies')),
        has_bankruptcy=_to_int(row.get('has_bankruptcy')),
        dti_ratio=_to_float(row.get('dti_ratio')),
        payment_to_income_ratio=_to_float(row.get('payment_to_income_ratio')),
        loan_rate=_to_float(row.get('loan_rate')),
        num_credit_contracts=_to_int(row.get('num_credit_contracts')),
        num_closed_loans=_to_int(row.get('num_closed_loans')),
        max_overdue_days=_to_int(row.get('max_overdue_days')),
        requested_amount=_to_float(row.get('requested_amount')),
        approved_amount=_to_float(row.get('approved_amount')),
        children_count=_to_int(row.get('children_count')),
        living_area_sqm=_to_float(row.get('living_area_sqm')),
        work_experience_total_years=_to_int(row.get('work_experience_total_years')),
        has_higher_education=_to_int(row.get('has_higher_education')),
        is_salary_client=_to_int(row.get('is_salary_client')),
        has_credit_card=_to_int(row.get('has_credit_card')),
        uses_mobile_banking=_to_int(row.get('uses_mobile_banking')),
        marital_status=_to_str(row.get('marital_status'), 'холост'),
        income_source=_to_str(row.get('income_source'), 'зарплата'),
        employment_type=_to_str(row.get('employment_type'), 'частный сектор'),
        position_level=_to_str(row.get('position_level'), 'специалист'),
        loan_purpose=_to_str(row.get('loan_purpose'), 'потребительский'),
        client_segment=_to_str(row.get('client_segment'), 'массовый'),
    )


def _predict_payload(client_data: ClientData) -> PredictionResponse:
    risk_label, confidence = predict_client_risk(client_data.model_dump(exclude_none=True))
    return PredictionResponse(
        risk_level=risk_label,
        confidence=round(float(confidence), 4),
        risk_description=RISK_DESCRIPTIONS.get(risk_label, 'Неизвестный уровень риска'),
    )


def _retention_summary(risk_level: str) -> str:
    if risk_level == 'forgot':
        return 'Отдельный удерживающий диалог не нужен: достаточно напоминаний и автоматизации платежа.'
    if risk_level == 'worried':
        return 'Откройте диалог поддержки: важно быстро предложить мягкое решение до выхода в устойчивую просрочку.'
    return 'Нужен отдельный антикризисный диалог с персональными предложениями и быстрым переводом на сопровождение.'


def _build_profile(row: dict[str, str], index: int) -> ClientProfileResponse:
    client_data = _row_to_client_data(row)
    risk = _predict_payload(client_data)
    return ClientProfileResponse(
        client_id=f'demo-client-{index}',
        full_name=_build_client_name(index),
        data=client_data,
        risk=risk,
        assistant_recommendations=ASSISTANT_RECOMMENDATIONS.get(risk.risk_level, []),
        retention_dialog_enabled=risk.risk_level != 'forgot',
        retention_summary=_retention_summary(risk.risk_level),
        retention_quick_replies=RETENTION_QUICK_REPLIES.get(risk.risk_level, []),
    )


def _retention_reply(request: RetentionChatRequest) -> RetentionChatResponse:
    message = request.message.lower()

    if request.risk_level == 'worried':
        if 'уменьш' in message or 'плат' in message:
            reply = (
                f'{request.client_name}, можем снизить нагрузку уже в ближайший платёжный цикл. '
                'Я предложу реструктуризацию с меньшим ежемесячным платежом и зафиксирую заявку менеджеру.'
            )
        elif 'доход' in message or 'зарплат' in message:
            reply = (
                f'{request.client_name}, вижу временное снижение дохода. '
                'Чтобы не доводить до просрочки, можно обсудить кредитные каникулы или перенос даты списания.'
            )
        else:
            reply = (
                f'{request.client_name}, давайте удержим договор в комфортном режиме. '
                'Я помогу подобрать мягкий сценарий: перенос даты платежа, уменьшение нагрузки или короткую отсрочку.'
            )

        next_steps = [
            'Предложить реструктуризацию на 3-6 месяцев.',
            'Проверить перенос даты списания ближе к дню поступления дохода.',
            'Подключить персонального менеджера без перевода кейса в жёсткое взыскание.',
        ]
        return RetentionChatResponse(reply=reply, next_steps=next_steps)

    if request.risk_level == 'bankruptcy':
        if 'сроч' in message or 'реструкт' in message:
            reply = (
                f'{request.client_name}, фиксирую срочный запрос на антикризисную реструктуризацию. '
                'Наша цель сейчас сохранить ваш договор активным и быстро снизить платёжную нагрузку.'
            )
        elif 'не хватает' in message or 'нечем' in message:
            reply = (
                f'{request.client_name}, спасибо, что сообщили заранее. '
                'В такой ситуации лучше сразу запустить защитный сценарий: пауза по штрафам, пересмотр графика и консультация специалиста.'
            )
        else:
            reply = (
                f'{request.client_name}, вижу высокий риск срыва платежей, но ещё есть пространство для решения. '
                'Сейчас предложу меры, которые помогут удержать договор и не допустить полного дефолта.'
            )

        next_steps = [
            'Срочно передать кейс в приоритетное сопровождение.',
            'Подготовить предложение по снижению платежа или временной паузе.',
            'Собрать подтверждение дохода и обновить финансовый профиль клиента.',
        ]
        return RetentionChatResponse(reply=reply, next_steps=next_steps)

    return RetentionChatResponse(
        reply='По этому клиенту достаточно мягких напоминаний и автоматизации платежа, отдельный кризисный сценарий не требуется.',
        next_steps=[
            'Настроить автоплатёж.',
            'Отправить напоминание перед датой списания.',
            'Предложить клиенту удобную дату платежа.',
        ],
    )


@app.get('/')
async def root():
    return {
        'status': 'online',
        'service': 'Sber Risk API',
        'version': '1.1.0',
        'endpoints': ['/client-profile', '/predict', '/retention-chat', '/health'],
    }


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'Sber Risk API'}


@app.get('/client-profile', response_model=ClientProfileResponse)
async def get_client_profile():
    try:
        index = random.randrange(len(DATASET_ROWS))
        return _build_profile(DATASET_ROWS[index], index)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f'Ошибка формирования профиля клиента: {error}') from error


@app.post('/predict', response_model=PredictionResponse)
async def predict_risk(client: ClientData):
    try:
        return _predict_payload(client)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f'Ошибка анализа риска: {error}') from error


@app.post('/retention-chat', response_model=RetentionChatResponse)
async def retention_chat(request: RetentionChatRequest):
    try:
        return _retention_reply(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f'Ошибка удерживающего диалога: {error}') from error


if __name__ == '__main__':
    uvicorn.run('main:app', port=8000, reload=True)
