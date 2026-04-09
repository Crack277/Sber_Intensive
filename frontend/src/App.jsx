import { useMemo, useState } from 'react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const tabs = [
  { id: 'main', label: 'Главная' },
  { id: 'payments', label: 'Платежи' },
  { id: 'credits', label: 'Кредиты' },
  { id: 'analytics', label: 'Аналитика' },
];

const quickActions = [
  { icon: '↗', title: 'Перевод' },
  { icon: '◉', title: 'Оплатить' },
  { icon: '◎', title: 'История' },
  { icon: '⌁', title: 'Поддержка' },
];

const products = [
  { title: 'СберКарта', subtitle: 'зарплатный счёт • 8452', amount: 184520, tone: 'emerald' },
  { title: 'Кредитная карта', subtitle: 'льготный период 12 дней', amount: -199999.69, tone: 'graphite' },
  { title: 'Накопительный счёт', subtitle: 'ставка 14.5% годовых', amount: 326400, tone: 'mint' },
];

const transactions = [
  { title: 'Погашение кредита', meta: 'Сегодня • автосписание', amount: -24500, badge: 'Кредит' },
  { title: 'Зарплата ООО Проект', meta: 'Сегодня • входящий перевод', amount: 98000, badge: 'Доход' },
  { title: 'Монетка', meta: 'Сегодня • продукты', amount: -2198.45, badge: 'Покупка' },
];

const assistantPrompts = {
  forgot: [
    'Напомнить клиенту о платеже за 3 и за 1 день до даты списания.',
    'Предложить автоплатёж или перенос даты списания под день зарплаты.',
    'Оставить мягкий контактный сценарий без давления и штрафных мер.',
  ],
  worried: [
    'Проверить возможность кредитных каникул или частичной реструктуризации.',
    'Снизить ежемесячную нагрузку за счёт пересмотра графика.',
    'Подключить менеджера с персональным сценарием удержания клиента.',
  ],
  bankruptcy: [
    'Передать кейс в приоритетную обработку службы сопровождения.',
    'Собрать документы по доходу, занятости и текущей долговой нагрузке.',
    'Предложить антикризисный план: реструктуризация, пауза, снижение платежа.',
  ],
};

const scenarioLabels = {
  forgot: 'Низкий риск',
  worried: 'Средний риск',
  bankruptcy: 'Высокий риск',
};

const scenarioThemes = {
  forgot: {
    tone: 'positive',
    title: 'Клиент скорее всего не проблемный',
    subtitle: 'Платёжная дисциплина в норме, риск связан скорее с забывчивостью.',
  },
  worried: {
    tone: 'warning',
    title: 'Есть признаки финансового напряжения',
    subtitle: 'Стоит предложить мягкое сопровождение и пересмотр условий.',
  },
  bankruptcy: {
    tone: 'critical',
    title: 'Требуется раннее вмешательство',
    subtitle: 'Модель видит высокий шанс серьёзной просрочки или ухода в дефолт.',
  },
};

function formatMoney(value) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function getRandomItem(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function generateRandomClient() {
  const scenarios = ['forgot', 'worried', 'bankruptcy'];
  const scenario = getRandomItem(scenarios);

  if (scenario === 'bankruptcy') {
    return {
      scenario,
      data: {
        monthly_payment: Math.round(Math.random() * 30000 + 28000),
        monthly_income: Math.round(Math.random() * 18000 + 18000),
        total_expenses: Math.round(Math.random() * 12000 + 14000),
        tenure_months: Math.floor(Math.random() * 12 + 4),
        total_overdue_days: Math.floor(Math.random() * 70 + 45),
        age: Math.floor(Math.random() * 18 + 34),
        credit_score: Math.floor(Math.random() * 180 + 320),
        num_loans: Math.floor(Math.random() * 4 + 3),
        employment_years: Number((Math.random() * 3 + 1).toFixed(1)),
        num_past_delinquencies: Math.floor(Math.random() * 5 + 3),
        has_bankruptcy: 1,
        dti_ratio: Number((Math.random() * 0.3 + 0.62).toFixed(2)),
        payment_to_income_ratio: Number((Math.random() * 0.25 + 0.52).toFixed(2)),
        loan_rate: Number((Math.random() * 9 + 24).toFixed(1)),
        num_credit_contracts: Math.floor(Math.random() * 4 + 4),
        num_closed_loans: Math.floor(Math.random() * 2),
        max_overdue_days: Math.floor(Math.random() * 90 + 50),
        requested_amount: Math.round(Math.random() * 320000 + 280000),
        approved_amount: Math.round(Math.random() * 220000 + 180000),
        children_count: Math.floor(Math.random() * 3 + 1),
        living_area_sqm: Math.round(Math.random() * 30 + 35),
        work_experience_total_years: Math.floor(Math.random() * 6 + 3),
        has_higher_education: Math.random() > 0.65 ? 1 : 0,
        is_salary_client: 0,
        has_credit_card: 1,
        uses_mobile_banking: 1,
        marital_status: getRandomItem(['разведён', 'холост']),
        income_source: getRandomItem(['самозанятость', 'бизнес']),
        employment_type: getRandomItem(['самозанятый', 'ИП']),
        position_level: 'специалист',
        loan_purpose: getRandomItem(['неотложные расходы', 'ремонт']),
        client_segment: 'массовый',
      },
    };
  }

  if (scenario === 'worried') {
    return {
      scenario,
      data: {
        monthly_payment: Math.round(Math.random() * 16000 + 14000),
        monthly_income: Math.round(Math.random() * 24000 + 42000),
        total_expenses: Math.round(Math.random() * 18000 + 24000),
        tenure_months: Math.floor(Math.random() * 24 + 12),
        total_overdue_days: Math.floor(Math.random() * 28 + 8),
        age: Math.floor(Math.random() * 15 + 30),
        credit_score: Math.floor(Math.random() * 160 + 520),
        num_loans: Math.floor(Math.random() * 3 + 2),
        employment_years: Number((Math.random() * 5 + 3).toFixed(1)),
        num_past_delinquencies: Math.floor(Math.random() * 3 + 1),
        has_bankruptcy: 0,
        dti_ratio: Number((Math.random() * 0.2 + 0.38).toFixed(2)),
        payment_to_income_ratio: Number((Math.random() * 0.18 + 0.28).toFixed(2)),
        loan_rate: Number((Math.random() * 8 + 18).toFixed(1)),
        num_credit_contracts: Math.floor(Math.random() * 3 + 2),
        num_closed_loans: Math.floor(Math.random() * 3 + 1),
        max_overdue_days: Math.floor(Math.random() * 18 + 12),
        requested_amount: Math.round(Math.random() * 220000 + 180000),
        approved_amount: Math.round(Math.random() * 180000 + 150000),
        children_count: Math.floor(Math.random() * 2 + 1),
        living_area_sqm: Math.round(Math.random() * 35 + 48),
        work_experience_total_years: Math.floor(Math.random() * 8 + 5),
        has_higher_education: Math.random() > 0.5 ? 1 : 0,
        is_salary_client: Math.random() > 0.45 ? 1 : 0,
        has_credit_card: 1,
        uses_mobile_banking: 1,
        marital_status: getRandomItem(['женат', 'холост']),
        income_source: 'зарплата',
        employment_type: getRandomItem(['частный сектор', 'госслужащий']),
        position_level: getRandomItem(['специалист', 'руководитель']),
        loan_purpose: getRandomItem(['ремонт', 'авто']),
        client_segment: getRandomItem(['массовый', 'масс-премиум']),
      },
    };
  }

  return {
    scenario,
    data: {
      monthly_payment: Math.round(Math.random() * 10000 + 10000),
      monthly_income: Math.round(Math.random() * 55000 + 78000),
      total_expenses: Math.round(Math.random() * 22000 + 36000),
      tenure_months: Math.floor(Math.random() * 30 + 24),
      total_overdue_days: Math.floor(Math.random() * 5),
      age: Math.floor(Math.random() * 18 + 28),
      credit_score: Math.floor(Math.random() * 120 + 720),
      num_loans: Math.floor(Math.random() * 2 + 1),
      employment_years: Number((Math.random() * 10 + 5).toFixed(1)),
      num_past_delinquencies: 0,
      has_bankruptcy: 0,
      dti_ratio: Number((Math.random() * 0.18 + 0.12).toFixed(2)),
      payment_to_income_ratio: Number((Math.random() * 0.12 + 0.1).toFixed(2)),
      loan_rate: Number((Math.random() * 7 + 11).toFixed(1)),
      num_credit_contracts: Math.floor(Math.random() * 2 + 1),
      num_closed_loans: Math.floor(Math.random() * 3 + 3),
      max_overdue_days: Math.floor(Math.random() * 4),
      requested_amount: Math.round(Math.random() * 160000 + 90000),
      approved_amount: Math.round(Math.random() * 140000 + 90000),
      children_count: Math.floor(Math.random() * 2),
      living_area_sqm: Math.round(Math.random() * 40 + 68),
      work_experience_total_years: Math.floor(Math.random() * 10 + 8),
      has_higher_education: 1,
      is_salary_client: 1,
      has_credit_card: 1,
      uses_mobile_banking: 1,
      marital_status: 'женат',
      income_source: 'зарплата',
      employment_type: getRandomItem(['госслужащий', 'частный сектор']),
      position_level: getRandomItem(['руководитель', 'топ-менеджер']),
      loan_purpose: getRandomItem(['авто', 'обучение']),
      client_segment: getRandomItem(['масс-премиум', 'премиум']),
    },
  };
}

function App() {
  const [activeTab, setActiveTab] = useState('main');
  const [showAssistant, setShowAssistant] = useState(true);
  const [generatedClient, setGeneratedClient] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content:
        'Я собрал для вас витрину риска клиента: могу сгенерировать профиль, отправить его в модель и сразу предложить сценарий помощи.',
    },
  ]);

  const assistantRecommendations = useMemo(() => {
    if (!riskAnalysis?.risk_level) {
      return [
        'Сгенерируйте клиента, чтобы показать demo-сценарий работы модели.',
        'После анализа интерфейс подскажет, как действовать с этим клиентом.',
        'Если API временно недоступен, UI аккуратно покажет ошибку вместо поломанного состояния.',
      ];
    }

    return assistantPrompts[riskAnalysis.risk_level] ?? [];
  }, [riskAnalysis]);

  const profileTheme = useMemo(() => {
    const scenario = riskAnalysis?.risk_level ?? generatedClient?.scenario ?? 'forgot';
    return scenarioThemes[scenario];
  }, [generatedClient, riskAnalysis]);

  const appendMessage = (content) => {
    setMessages((prev) => [...prev, { type: 'bot', content }]);
  };

  const handleGenerateClient = () => {
    const nextClient = generateRandomClient();
    setGeneratedClient(nextClient);
    setRiskAnalysis(null);
    setShowAssistant(true);
    appendMessage(
      `Сформирован тестовый профиль: ${scenarioLabels[nextClient.scenario]}. Можно отправлять в модель и разбирать меры поддержки клиента.`
    );
  };

  const handleAnalyzeRisk = async () => {
    if (!generatedClient) {
      appendMessage('Сначала нужен профиль клиента. Сгенерируйте его, и я отправлю данные в модель.');
      return;
    }

    setIsLoading(true);
    appendMessage('Отправляю профиль в модель риска и собираю интерпретацию результата.');

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(generatedClient.data),
      });

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = payload?.detail || 'Сервер вернул ошибку при анализе профиля.';
        throw new Error(detail);
      }

      setRiskAnalysis(payload);
      appendMessage(
        `Модель вернула уровень "${scenarioLabels[payload.risk_level] ?? payload.risk_level}". Уверенность: ${(
          payload.confidence * 100
        ).toFixed(1)}%. ${payload.risk_description}`
      );
    } catch (error) {
      appendMessage(
        `Не удалось получить ответ от API. ${error.message}. Проверьте backend на ${API_URL} и повторите запрос.`
      );
    } finally {
      setIsLoading(false);
    }
  };

  const riskLevel = riskAnalysis?.risk_level ?? generatedClient?.scenario;

  return (
    <div className="app-shell">
      <div className="app">
        <header className="header">
          <div className="topbar">
            <div>
              <div className="brand-row">
                <div className="brand-mark" aria-hidden="true">
                  <span className="brand-core" />
                </div>
                <div>
                  <p className="brand-eyebrow">Сбер ID</p>
                  <h1 className="brand-title">Иван, добрый вечер</h1>
                </div>
              </div>
              <p className="brand-subtitle">
                Банк, ассистент и скоринг риска в одном клиентском интерфейсе
              </p>
            </div>

            <div className="header-actions">
              <button
                className={`icon-btn ${showAssistant ? 'active' : ''}`}
                type="button"
                onClick={() => setShowAssistant((prev) => !prev)}
                aria-label="Переключить ассистента"
              >
                AI
              </button>
              <button className="icon-btn" type="button" aria-label="Уведомления">
                ⌁
              </button>
              <button className="icon-btn" type="button" aria-label="Профиль">
                И
              </button>
            </div>
          </div>

          <nav className="header-tabs" aria-label="Разделы">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </header>

        <main className="main-content">
          <section className="hero-card">
            <div className="hero-copy">
              <span className="hero-label">Платёжный календарь</span>
              <h2>Минимальный платёж до 30 апреля</h2>
              <p>
                Интерфейс сразу поднимает риск-сигнал и предлагает перейти к сценарию
                удержания клиента через AI-помощника.
              </p>
            </div>
            <div className="hero-stats">
              <div>
                <span className="stat-label">Сумма платежа</span>
                <strong>{formatMoney(199999.69)}</strong>
              </div>
              <div>
                <span className="stat-label">Вероятность риска</span>
                <strong>{riskAnalysis ? formatPercent(riskAnalysis.confidence) : 'н/д'}</strong>
              </div>
            </div>
            <div className="hero-actions">
              <button type="button" className="primary-btn" onClick={() => setShowAssistant(true)}>
                Открыть ассистента
              </button>
              <button type="button" className="secondary-btn" onClick={handleGenerateClient}>
                Новый клиент
              </button>
            </div>
          </section>

          {showAssistant && (
            <section className={`assistant-panel ${profileTheme.tone}`}>
              <div className="assistant-heading">
                <div>
                  <span className="assistant-label">Sber Risk Assistant</span>
                  <h3>{profileTheme.title}</h3>
                  <p>{profileTheme.subtitle}</p>
                </div>
                {riskLevel && (
                  <span className={`risk-pill risk-pill-${riskLevel}`}>
                    {scenarioLabels[riskLevel]}
                  </span>
                )}
              </div>

              <div className="assistant-grid">
                <div className="assistant-chat">
                  {messages.slice(-4).map((message, index) => (
                    <article key={`${message.content}-${index}`} className="assistant-message">
                      <div className="assistant-avatar">AI</div>
                      <div className="assistant-bubble">
                        <p>{message.content}</p>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="assistant-actions">
                  <button type="button" className="primary-btn" onClick={handleGenerateClient}>
                    Сгенерировать профиль
                  </button>
                  <button
                    type="button"
                    className="secondary-btn accent"
                    onClick={handleAnalyzeRisk}
                    disabled={!generatedClient || isLoading}
                  >
                    {isLoading ? 'Анализируем...' : 'Запустить скоринг'}
                  </button>
                  <p className="assistant-note">
                    API: <span>{API_URL}</span>
                  </p>
                </div>
              </div>

              <div className="insights-grid">
                <article className="insight-card">
                  <span className="insight-label">Профиль клиента</span>
                  {generatedClient ? (
                    <dl className="detail-list">
                      <div>
                        <dt>Доход</dt>
                        <dd>{formatMoney(generatedClient.data.monthly_income)}</dd>
                      </div>
                      <div>
                        <dt>Платёж</dt>
                        <dd>{formatMoney(generatedClient.data.monthly_payment)}</dd>
                      </div>
                      <div>
                        <dt>DTI</dt>
                        <dd>{formatPercent(generatedClient.data.dti_ratio)}</dd>
                      </div>
                      <div>
                        <dt>Просрочка</dt>
                        <dd>{generatedClient.data.total_overdue_days} дней</dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="empty-copy">Пока нет активного профиля. Сгенерируйте демо-клиента.</p>
                  )}
                </article>

                <article className="insight-card">
                  <span className="insight-label">Рекомендации ассистента</span>
                  <div className="recommendation-list">
                    {assistantRecommendations.map((item) => (
                      <p key={item}>{item}</p>
                    ))}
                  </div>
                </article>

                <article className="insight-card">
                  <span className="insight-label">Вердикт модели</span>
                  {riskAnalysis ? (
                    <div className="model-summary">
                      <strong>{scenarioLabels[riskAnalysis.risk_level]}</strong>
                      <p>{riskAnalysis.risk_description}</p>
                      <span>Уверенность модели: {formatPercent(riskAnalysis.confidence)}</span>
                    </div>
                  ) : (
                    <p className="empty-copy">
                      После запуска скоринга здесь появится расшифровка результата от backend-модели.
                    </p>
                  )}
                </article>
              </div>
            </section>
          )}

          <section className="section-card">
            <div className="section-heading">
              <div>
                <span className="section-label">Финансы</span>
                <h3>Кошелёк и продукты</h3>
              </div>
              <button type="button" className="ghost-link">
                Все счета
              </button>
            </div>

            <div className="product-list">
              {products.map((product) => (
                <article key={product.title} className={`product-card ${product.tone}`}>
                  <div>
                    <h4>{product.title}</h4>
                    <p>{product.subtitle}</p>
                  </div>
                  <strong>{formatMoney(product.amount)}</strong>
                </article>
              ))}
            </div>
          </section>

          <section className="section-card compact">
            <div className="section-heading">
              <div>
                <span className="section-label">Сценарии</span>
                <h3>{tabs.find((tab) => tab.id === activeTab)?.label}</h3>
              </div>
            </div>

            <div className="actions-grid">
              {quickActions.map((action) => (
                <button key={action.title} type="button" className="action-btn">
                  <span className="action-icon">{action.icon}</span>
                  <span>{action.title}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="section-card">
            <div className="section-heading">
              <div>
                <span className="section-label">Лента</span>
                <h3>Последние операции</h3>
              </div>
              <button type="button" className="ghost-link">
                Вся история
              </button>
            </div>

            <div className="transaction-list">
              {transactions.map((transaction) => (
                <article key={transaction.title} className="transaction-item">
                  <div className="transaction-badge">{transaction.badge}</div>
                  <div className="transaction-copy">
                    <h4>{transaction.title}</h4>
                    <p>{transaction.meta}</p>
                  </div>
                  <strong className={transaction.amount > 0 ? 'positive' : ''}>
                    {transaction.amount > 0 ? '+' : ''}
                    {formatMoney(transaction.amount)}
                  </strong>
                </article>
              ))}
            </div>
          </section>
        </main>

        <nav className="bottom-nav" aria-label="Нижняя навигация">
          <button type="button" className="nav-item active">
            <span>Главная</span>
          </button>
          <button type="button" className="nav-item">
            <span>Платежи</span>
          </button>
          <button type="button" className="nav-item">
            <span>История</span>
          </button>
          <button type="button" className="nav-item">
            <span>Профиль</span>
          </button>
        </nav>
      </div>
    </div>
  );
}

export default App;
