import { useState } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('main');
  const [showKotAssistant, setShowKotAssistant] = useState(false);
  const [generatedClient, setGeneratedClient] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [kotMessages, setKotMessages] = useState([
    {
      type: 'bot',
      avatar: '🐱',
      content: 'Мяу! 👋 Я СберКот - ваш AI-помощник по оценке кредитных рисков. Нажмите кнопку ниже, чтобы сгенерировать тестового клиента и получить анализ.'
    }
  ]);

  // API URL (можно вынести в .env)
  const API_URL = 'http://localhost:8000';

  // Функция генерации случайного клиента
  const generateRandomClient = () => {
    const scenarios = ['forgot', 'worried', 'bankruptcy'];
    const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];

    let clientData;

    switch(scenario) {
      case 'bankruptcy':
        clientData = {
          monthly_payment: Math.round(Math.random() * 30000 + 25000),
          monthly_income: Math.round(Math.random() * 15000 + 15000),
          total_expenses: Math.round(Math.random() * 10000 + 12000),
          tenure_months: Math.floor(Math.random() * 12 + 3),
          total_overdue_days: Math.floor(Math.random() * 60 + 60),
          age: Math.floor(Math.random() * 20 + 35),
          credit_score: Math.floor(Math.random() * 200 + 300),
          num_loans: Math.floor(Math.random() * 5 + 3),
          employment_years: Math.random() * 3 + 1,
          num_past_delinquencies: Math.floor(Math.random() * 6 + 3),
          has_bankruptcy: 1,
          dti_ratio: Math.random() * 0.4 + 0.6,
          payment_to_income_ratio: Math.random() * 0.4 + 0.5,
          loan_rate: Math.random() * 10 + 25,
          num_credit_contracts: Math.floor(Math.random() * 4 + 4),
          num_closed_loans: Math.floor(Math.random() * 2),
          max_overdue_days: Math.floor(Math.random() * 60 + 60),
          requested_amount: Math.round(Math.random() * 300000 + 300000),
          approved_amount: Math.round(Math.random() * 200000 + 250000),
          children_count: Math.floor(Math.random() * 3 + 1),
          living_area_sqm: Math.round(Math.random() * 30 + 30),
          work_experience_total_years: Math.floor(Math.random() * 5 + 3),
          has_higher_education: Math.random() > 0.7 ? 1 : 0,
          is_salary_client: 0,
          has_credit_card: 1,
          uses_mobile_banking: 1,
          marital_status: ['разведен', 'холост'][Math.floor(Math.random() * 2)],
          income_source: ['самозанятый', 'бизнес'][Math.floor(Math.random() * 2)],
          employment_type: ['самозанятый', 'ИП'][Math.floor(Math.random() * 2)],
          position_level: 'специалист',
          loan_purpose: ['неотложные нужды', 'ремонт'][Math.floor(Math.random() * 2)],
          client_segment: 'массовый'
        };
        break;

      case 'worried':
        clientData = {
          monthly_payment: Math.round(Math.random() * 15000 + 15000),
          monthly_income: Math.round(Math.random() * 20000 + 40000),
          total_expenses: Math.round(Math.random() * 15000 + 25000),
          tenure_months: Math.floor(Math.random() * 24 + 12),
          total_overdue_days: Math.floor(Math.random() * 30 + 10),
          age: Math.floor(Math.random() * 15 + 30),
          credit_score: Math.floor(Math.random() * 150 + 500),
          num_loans: Math.floor(Math.random() * 3 + 2),
          employment_years: Math.random() * 5 + 3,
          num_past_delinquencies: Math.floor(Math.random() * 3 + 1),
          has_bankruptcy: 0,
          dti_ratio: Math.random() * 0.3 + 0.4,
          payment_to_income_ratio: Math.random() * 0.2 + 0.3,
          loan_rate: Math.random() * 10 + 18,
          num_credit_contracts: Math.floor(Math.random() * 3 + 2),
          num_closed_loans: Math.floor(Math.random() * 3 + 1),
          max_overdue_days: Math.floor(Math.random() * 20 + 15),
          requested_amount: Math.round(Math.random() * 200000 + 200000),
          approved_amount: Math.round(Math.random() * 150000 + 180000),
          children_count: Math.floor(Math.random() * 2 + 1),
          living_area_sqm: Math.round(Math.random() * 40 + 50),
          work_experience_total_years: Math.floor(Math.random() * 8 + 5),
          has_higher_education: Math.random() > 0.5 ? 1 : 0,
          is_salary_client: Math.random() > 0.5 ? 1 : 0,
          has_credit_card: 1,
          uses_mobile_banking: 1,
          marital_status: ['женат', 'холост'][Math.floor(Math.random() * 2)],
          income_source: 'зарплата',
          employment_type: ['частный сектор', 'госслужащий'][Math.floor(Math.random() * 2)],
          position_level: ['специалист', 'руководитель'][Math.floor(Math.random() * 2)],
          loan_purpose: ['ремонт', 'авто'][Math.floor(Math.random() * 2)],
          client_segment: ['массовый', 'масс-премиум'][Math.floor(Math.random() * 2)]
        };
        break;

      default: // forgot
        clientData = {
          monthly_payment: Math.round(Math.random() * 10000 + 10000),
          monthly_income: Math.round(Math.random() * 50000 + 80000),
          total_expenses: Math.round(Math.random() * 20000 + 40000),
          tenure_months: Math.floor(Math.random() * 36 + 24),
          total_overdue_days: Math.floor(Math.random() * 5),
          age: Math.floor(Math.random() * 20 + 28),
          credit_score: Math.floor(Math.random() * 150 + 700),
          num_loans: Math.floor(Math.random() * 2 + 1),
          employment_years: Math.random() * 10 + 5,
          num_past_delinquencies: 0,
          has_bankruptcy: 0,
          dti_ratio: Math.random() * 0.2 + 0.15,
          payment_to_income_ratio: Math.random() * 0.15 + 0.1,
          loan_rate: Math.random() * 8 + 12,
          num_credit_contracts: Math.floor(Math.random() * 2 + 1),
          num_closed_loans: Math.floor(Math.random() * 3 + 3),
          max_overdue_days: Math.floor(Math.random() * 5),
          requested_amount: Math.round(Math.random() * 150000 + 100000),
          approved_amount: Math.round(Math.random() * 150000 + 100000),
          children_count: Math.floor(Math.random() * 2),
          living_area_sqm: Math.round(Math.random() * 50 + 70),
          work_experience_total_years: Math.floor(Math.random() * 10 + 8),
          has_higher_education: 1,
          is_salary_client: 1,
          has_credit_card: 1,
          uses_mobile_banking: 1,
          marital_status: 'женат',
          income_source: 'зарплата',
          employment_type: ['госслужащий', 'частный сектор'][Math.floor(Math.random() * 2)],
          position_level: ['руководитель', 'топ-менеджер'][Math.floor(Math.random() * 2)],
          loan_purpose: ['авто', 'обучение'][Math.floor(Math.random() * 2)],
          client_segment: ['масс-премиум', 'премиум'][Math.floor(Math.random() * 2)]
        };
    }

    return { data: clientData, scenario };
  };

  // Обработчик генерации клиента
  const handleGenerateClient = () => {
    const { data, scenario } = generateRandomClient();
    setGeneratedClient(data);
    setRiskAnalysis(null);

    // Добавляем сообщение в чат
    const scenarioNames = {
      'bankruptcy': '🔴 ВЫСОКИЙ РИСК',
      'worried': '🟡 СРЕДНИЙ РИСК',
      'forgot': '🟢 НИЗКИЙ РИСК'
    };

    setKotMessages(prev => [...prev, {
      type: 'bot',
      avatar: '🐱',
      content: `Сгенерирован новый клиент (${scenarioNames[scenario]})`
    }]);

    setShowKotAssistant(true);
  };

  // Обработчик анализа риска
  const handleAnalyzeRisk = async () => {
    if (!generatedClient) return;

    setIsLoading(true);
    setKotMessages(prev => [...prev, {
      type: 'bot',
      avatar: '🐱',
      content: '🔍 Анализирую профиль клиента...'
    }]);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(generatedClient)
      });

      if (!response.ok) {
        throw new Error('Ошибка при анализе');
      }

      const result = await response.json();
      setRiskAnalysis(result);

      // Добавляем результат в чат
      const riskEmoji = {
        'forgot': '🟢',
        'worried': '🟡',
        'bankruptcy': '🔴'
      };

      const riskNames = {
        'forgot': 'НИЗКИЙ РИСК (забыл)',
        'worried': 'СРЕДНИЙ РИСК (волнуется)',
        'bankruptcy': 'ВЫСОКИЙ РИСК (банкротство)'
      };

      setKotMessages(prev => [...prev, {
        type: 'bot',
        avatar: '🐱',
        content: `${riskEmoji[result.risk_level]} Результат анализа: ${riskNames[result.risk_level]}\n\n${result.risk_description}\n\nУверенность: ${(result.confidence * 100).toFixed(1)}%`
      }]);

    } catch (error) {
      console.error('Ошибка:', error);
      setKotMessages(prev => [...prev, {
        type: 'bot',
        avatar: '🐱',
        content: '❌ Ошибка при анализе. Проверьте, запущен ли сервер.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Форматирование значений для отображения
  const formatMoney = (value) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-top">
          <div className="logo">
            <span className="logo-icon">🏦</span>
            <span className="logo-text">СБЕРБАНК</span>
          </div>
          <div className="header-actions">
            <button
              className={`icon-btn ${showKotAssistant ? 'active' : ''}`}
              onClick={() => setShowKotAssistant(!showKotAssistant)}
              title="СберКот - анализ рисков"
            >
              🐱
            </button>
            <button className="icon-btn">🔔</button>
            <button className="icon-btn">👤</button>
          </div>
        </div>
        <div className="header-tabs">
          <button className={`tab ${activeTab === 'main' ? 'active' : ''}`}>Главный</button>
          <button className={`tab ${activeTab === 'savings' ? 'active' : ''}`}>Накопления</button>
          <button className={`tab ${activeTab === 'payments' ? 'active' : ''}`}>Платежи</button>
          <button className={`tab ${activeTab === 'credits' ? 'active' : ''}`}>Кредиты</button>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        <div className="container">
          {/* СберКот Assistant */}
          {showKotAssistant && (
            <div className="kot-assistant">
              <div className="kot-header">
                <div className="kot-title">
                  <span className="kot-icon">🐱</span>
                  <h3>СберКот • Анализ рисков</h3>
                </div>
                <button
                  className="kot-close"
                  onClick={() => setShowKotAssistant(false)}
                >
                  ✕
                </button>
              </div>

              <div className="kot-chat">
                {kotMessages.slice(-5).map((msg, idx) => (
                  <div key={idx} className={`kot-message kot-message-${msg.type}`}>
                    <div className="kot-message-avatar">{msg.avatar}</div>
                    <div className="kot-message-content">
                      {msg.content.split('\n').map((line, i) => (
                        <p key={i}>{line}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="kot-actions">
                <button
                  className="kot-btn kot-btn-generate"
                  onClick={handleGenerateClient}
                >
                  <span>🎲</span>
                  Сгенерировать клиента
                </button>
                <button
                  className="kot-btn kot-btn-analyze"
                  onClick={handleAnalyzeRisk}
                  disabled={!generatedClient || isLoading}
                >
                  <span>{isLoading ? '⏳' : '🔮'}</span>
                  {isLoading ? 'Анализ...' : 'Анализировать'}
                </button>
              </div>

              {generatedClient && (
                <div className="kot-client-card">
                  <div className="kot-client-header">
                    <h4>📋 Профиль клиента</h4>
                    {riskAnalysis && (
                      <span className={`kot-risk-badge kot-risk-${riskAnalysis.risk_level}`}>
                        {riskAnalysis.risk_level === 'forgot' && '🟢 Низкий риск'}
                        {riskAnalysis.risk_level === 'worried' && '🟡 Средний риск'}
                        {riskAnalysis.risk_level === 'bankruptcy' && '🔴 Высокий риск'}
                      </span>
                    )}
                  </div>
                  <div className="kot-client-details">
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">Доход:</span>
                      <span className="kot-detail-value">{formatMoney(generatedClient.monthly_income)}</span>
                    </div>
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">Платеж:</span>
                      <span className="kot-detail-value">{formatMoney(generatedClient.monthly_payment)}</span>
                    </div>
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">Просрочка:</span>
                      <span className={`kot-detail-value ${generatedClient.total_overdue_days > 30 ? 'risk-high' : generatedClient.total_overdue_days > 10 ? 'risk-medium' : 'risk-low'}`}>
                        {generatedClient.total_overdue_days} дней
                      </span>
                    </div>
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">DTI:</span>
                      <span className="kot-detail-value">{formatPercent(generatedClient.dti_ratio)}</span>
                    </div>
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">Ставка:</span>
                      <span className="kot-detail-value">{generatedClient.loan_rate.toFixed(1)}%</span>
                    </div>
                    <div className="kot-detail-row">
                      <span className="kot-detail-label">Банкротство:</span>
                      <span className={`kot-detail-value ${generatedClient.has_bankruptcy ? 'risk-high' : ''}`}>
                        {generatedClient.has_bankruptcy ? 'ДА' : 'НЕТ'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Greeting and Search */}
          <div className="greeting-section">
            <h1>Здравствуйте, Иван!</h1>
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input type="text" placeholder="Поиск операций, платежей, переводов" />
            </div>
          </div>

          {/* Wallet Section */}
          <div className="wallet-section">
            <div className="section-header">
              <h2>Кошелёк</h2>
              <button className="link-btn">Все счета →</button>
            </div>

            {/* Main Balance Card */}
            <div className="main-balance-card">
              <div className="balance-header">
                <span className="balance-label">Внесите до 30.04</span>
                <span className="info-icon">ⓘ</span>
              </div>
              <div className="balance-amount">199 999,69 ₽</div>
              <div className="balance-footer-wrapper">
                <div className="min-payment-info">
                  <span className="balance-footer">Минимальный платёж</span>
                  <span className="min-payment-hint">до 30.04.2024</span>
                </div>
                <button
                  className="help-button help-button-attention"
                  onClick={() => {
                    setShowKotAssistant(true);
                    setKotMessages(prev => [...prev,
                      {
                        type: 'bot',
                        avatar: '🐱',
                        content: '👋 Здравствуйте! Я СберКот. Вижу, у вас есть минимальный платеж. Могу помочь разобраться с кредитной нагрузкой или предложить реструктуризацию.'
                      },
                      {
                        type: 'bot',
                        avatar: '🐱',
                        content: 'Нажмите "Сгенерировать клиента" для демонстрации анализа рисков или спросите меня о вашей ситуации.'
                      }
                    ]);
                  }}
                >
                  <span className="help-icon">🐱</span>
                  <span className="help-text">Спросить СберКота</span>
                  <span className="help-badge">●</span>
                </button>
              </div>
            </div>

            {/* Cards List */}
            <div className="cards-list">
              <div className="card-row">
                <div className="card-info">
                  <div className="card-icon">💳</div>
                  <div className="card-details">
                    <div className="card-name">Visa Classic</div>
                    <div className="card-number">•• 1234</div>
                  </div>
                </div>
                <div className="card-balance">-200 000 ₽</div>
              </div>

              <div className="card-row">
                <div className="card-info">
                  <div className="card-icon">💳</div>
                  <div className="card-details">
                    <div className="card-name">Кредитная</div>
                    <div className="card-number">•• 1234</div>
                  </div>
                </div>
                <div className="card-balance">20 000,36 ₽</div>
              </div>

              <div className="card-row">
                <div className="card-info">
                  <div className="card-icon">💳</div>
                  <div className="card-details">
                    <div className="card-name">МИР Классическая</div>
                    <div className="card-number">•• 1234</div>
                  </div>
                </div>
                <div className="card-balance">1 925,76 ₽</div>
              </div>
            </div>

            {/* SberSpasibo */}
            <div className="spasibo-card">
              <div className="spasibo-info">
                <span className="spasibo-icon">⭐</span>
                <span className="spasibo-text">СберСпасибо</span>
              </div>
              <div className="spasibo-balance">194</div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            <button className="action-btn">
              <div className="action-icon">📲</div>
              <span>Перевод</span>
            </button>
            <button className="action-btn">
              <div className="action-icon">💳</div>
              <span>Оплатить</span>
            </button>
            <button className="action-btn">
              <div className="action-icon">📊</div>
              <span>Аналитика</span>
            </button>
            <button className="action-btn">
              <div className="action-icon">🏷️</div>
              <span>Акции</span>
            </button>
          </div>

          {/* Investment Banner */}
          <div className="investment-banner">
            <div className="banner-content">
              <h3>Золотое будущее</h3>
              <p>Инвестируйте в драгметаллы от 0.1 г., не выходя из дома</p>
              <button className="banner-btn">Узнать</button>
            </div>
            <div className="banner-icon">💰</div>
          </div>

          {/* Recent Transactions */}
          <div className="transactions-section">
            <div className="section-header">
              <h2>История</h2>
              <button className="link-btn">Все →</button>
            </div>

            <div className="transactions-list">
              <div className="transaction-item">
                <div className="transaction-icon">🏢</div>
                <div className="transaction-details">
                  <div className="transaction-name">ООО "PROEKT" TOMSK RUS</div>
                  <div className="transaction-meta">Сегодня • Оплата товаров и услуг</div>
                </div>
                <div className="transaction-amount">38 ₽</div>
              </div>

              <div className="transaction-item">
                <div className="transaction-icon">🛒</div>
                <div className="transaction-details">
                  <div className="transaction-name">Монетка</div>
                  <div className="transaction-meta">Сегодня • Оплата товаров и услуг</div>
                </div>
                <div className="transaction-amount">99,98 ₽</div>
              </div>

              <div className="transaction-item">
                <div className="transaction-icon">🏢</div>
                <div className="transaction-details">
                  <div className="transaction-name">ООО PROEKT TOMSK RUS</div>
                  <div className="transaction-meta">Сегодня • Оплата товаров и услуг</div>
                </div>
                <div className="transaction-amount">36 ₽</div>
              </div>
            </div>
          </div>

          {/* Recent Transfers */}
          <div className="transfers-section">
            <div className="section-header">
              <h2>Последние переводы</h2>
              <button className="link-btn">Все →</button>
            </div>

            <div className="transfers-list">
              <div className="transfer-item">
                <div className="transfer-avatar">👩</div>
                <div className="transfer-details">
                  <div className="transfer-name">Лиза</div>
                  <div className="transfer-meta">Подтверждён • Сегодня</div>
                </div>
                <div className="transfer-amount positive">+1 200 ₽</div>
              </div>

              <div className="transfer-item">
                <div className="transfer-avatar">🐶</div>
                <div className="transfer-details">
                  <div className="transfer-name">Даша</div>
                  <div className="transfer-meta">Зачислено • Вчера</div>
                </div>
                <div className="transfer-amount">850 ₽</div>
              </div>

              <div className="transfer-item">
                <div className="transfer-avatar">И</div>
                <div className="transfer-details">
                  <div className="transfer-name">Ирина И.</div>
                  <div className="transfer-meta">По номеру телефона</div>
                </div>
                <div className="transfer-amount">2 500 ₽</div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Bottom Navigation */}
      <nav className="bottom-nav">
        <button className="nav-item active">
          <span>🏠</span>
          <span>Главный</span>
        </button>
        <button className="nav-item">
          <span>📊</span>
          <span>История</span>
        </button>
        <button className="nav-item">
          <span>💳</span>
          <span>Платежи</span>
        </button>
        <button className="nav-item">
          <span>👤</span>
          <span>Профиль</span>
        </button>
        <button className="nav-item">
          <span>☰</span>
          <span>Ещё</span>
        </button>
      </nav>
    </div>
  );
}

export default App;