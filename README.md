# Sber Intensive

Демо-проект банковского интерфейса с модулем оценки кредитного риска и сценариями удержания клиента.  
Проект состоит из фронтенда на React и backend API на FastAPI, которое загружает клиентские данные, рассчитывает риск и возвращает готовый профиль для интерфейса.

## Идея проекта

Приложение имитирует клиентский кабинет банка, где:

- отображается профиль клиента и его финансовые показатели
- оценивается вероятность проблем с выплатами
- определяется один из сценариев риска: `forgot`, `worried`, `bankruptcy`
- запускается демо-диалог удержания клиента в зависимости от уровня риска

## Состав репозитория

- `frontend/` - пользовательский интерфейс на React + Vite
- `backend/` - FastAPI API, модель риска и датасеты

## Основные возможности

- загрузка случайного профиля клиента из датасета
- отображение ключевых банковских данных: доход, платёж, продукты, история операций
- оценка риска с помощью обученной модели и дополнительных эвристик
- возврат рекомендаций для сопровождения клиента
- демо-чат для удерживающего сценария

## Технологии

Frontend:

- React
- Vite
- CSS

Backend:

- FastAPI
- Uvicorn
- Pydantic
- pandas
- numpy
- scikit-learn
- joblib

## Структура проекта

```text
Sber_Intensive/
|-- backend/
|   |-- main.py
|   |-- risk_predictor.py
|   |-- train_model.py
|   |-- generate_realistic_clients.py
|   |-- requirements.txt
|   |-- risk_model.pkl
|   |-- risk_model_metadata.json
|   |-- bank_clients_filtered.csv
|   `-- bank_clients_synthetic_realistic.csv
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- App.css
|   |   `-- main.jsx
|   |-- package.json
|   `-- vite.config.js
`-- README.md
```

## Быстрый старт

### Backend

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

После запуска API будет доступен по адресу `http://localhost:8000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

После запуска интерфейс будет доступен по адресу `http://localhost:5173`.

## Переменные окружения

Во фронтенде можно переопределить адрес backend:

```env
VITE_API_URL=http://localhost:8000
```

Если переменная не указана, используется `http://localhost:8000`.

## API

Основные эндпоинты:

- `GET /` - информация о сервисе
- `GET /health` - статус API
- `GET /client-profile` - случайный профиль клиента с риском и рекомендациями
- `POST /predict` - расчёт риска по входным данным клиента
- `POST /retention-chat` - ответ демо-ассистента для удержания клиента

## Как работает сценарий

1. Frontend запрашивает профиль клиента через `GET /client-profile`.
2. Backend читает данные клиента из CSV.
3. Модуль `risk_predictor.py` загружает обученную модель из `risk_model.pkl`.
4. API возвращает профиль, уровень риска, краткое описание и рекомендации.
5. Интерфейс показывает результат и открывает соответствующий сценарий диалога.

## Полезные файлы

- `backend/main.py` - основной FastAPI-сервер
- `backend/risk_predictor.py` - логика загрузки модели и предсказания риска
- `backend/train_model.py` - обучение модели
- `backend/generate_realistic_clients.py` - генерация синтетического датасета
