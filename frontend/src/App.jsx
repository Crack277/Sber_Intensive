import { useEffect, useMemo, useState } from 'react';
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

const scenarioLabels = {
  forgot: 'Низкий риск',
  worried: 'Средний риск',
  bankruptcy: 'Высокий риск',
};

const scenarioThemes = {
  forgot: {
    tone: 'positive',
  },
  worried: {
    tone: 'warning',
  },
  bankruptcy: {
    tone: 'critical',
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

function App() {
  const [activeTab, setActiveTab] = useState('main');
  const [showAssistant, setShowAssistant] = useState(true);
  const [isBotDialogOpen, setIsBotDialogOpen] = useState(false);
  const [clientProfile, setClientProfile] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [retentionMessages, setRetentionMessages] = useState([]);
  const [retentionInput, setRetentionInput] = useState('');
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isRetentionLoading, setIsRetentionLoading] = useState(false);

  const profileTheme = useMemo(() => {
    const scenario = riskAnalysis?.risk_level ?? 'forgot';
    return scenarioThemes[scenario];
  }, [riskAnalysis]);

  const openBotDialog = () => {
    setIsBotDialogOpen(true);
  };

  const closeBotDialog = () => {
    setIsBotDialogOpen(false);
  };

  const loadClientProfile = async () => {
    setIsLoadingProfile(true);

    try {
      const response = await fetch(`${API_URL}/client-profile`);
      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(payload?.detail || 'Не удалось получить профиль клиента.');
      }

      setClientProfile(payload);
      setRiskAnalysis(payload.risk);
      setRetentionMessages(
        payload.retention_dialog_enabled
          ? [
              {
                type: 'bot',
                content: payload.retention_summary,
              },
            ]
          : []
      );
      setRetentionInput('');
      setShowAssistant(true);
      setIsBotDialogOpen(false);
    } catch (error) {
      console.error('Failed to load client profile', error);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  useEffect(() => {
    loadClientProfile();
  }, []);

  const handleRetentionSubmit = async (prefilledMessage) => {
    const message = (prefilledMessage ?? retentionInput).trim();

    if (!message || !clientProfile || !riskAnalysis) {
      return;
    }

    setIsRetentionLoading(true);
    setRetentionMessages((prev) => [...prev, { type: 'user', content: message }]);
    setRetentionInput('');

    try {
      const response = await fetch(`${API_URL}/retention-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: clientProfile.client_id,
          client_name: clientProfile.full_name,
          risk_level: riskAnalysis.risk_level,
          message,
        }),
      });

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(payload?.detail || 'Не удалось получить ответ удерживающего бота.');
      }

      setRetentionMessages((prev) => [
        ...prev,
        { type: 'bot', content: payload.reply },
        ...payload.next_steps.map((item) => ({ type: 'bot-tip', content: item })),
      ]);
    } catch (error) {
      setRetentionMessages((prev) => [
        ...prev,
        {
          type: 'bot',
          content: `Удерживающий бот временно недоступен. ${error.message}`,
        },
      ]);
    } finally {
      setIsRetentionLoading(false);
    }
  };

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
                  <h1 className="brand-title">
                    {clientProfile ? `${clientProfile.full_name}, добрый вечер` : 'Клиент, добрый вечер'}
                  </h1>
                </div>
              </div>
              <p className="brand-subtitle">
                Клиентский интерфейс с данными профиля, платежами и историей операций.
              </p>
            </div>

            <div className="header-actions">
              <button
                className={`icon-btn ${isBotDialogOpen ? 'active' : ''}`}
                type="button"
                onClick={openBotDialog}
                aria-label="Открыть диалог"
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
              <p>В интерфейсе отображаются только данные клиента без рекомендаций ассистента и оценки риска.</p>
            </div>
            <div className="hero-stats">
              <div>
                <span className="stat-label">Ежемесячный платёж</span>
                <strong>
                  {clientProfile ? formatMoney(clientProfile.data.monthly_payment) : formatMoney(0)}
                </strong>
              </div>
              <div>
                <span className="stat-label">Ежемесячный доход</span>
                <strong>
                  {clientProfile ? formatMoney(clientProfile.data.monthly_income) : formatMoney(0)}
                </strong>
              </div>
            </div>
            <div className="hero-actions">
              <button type="button" className="primary-btn" onClick={loadClientProfile}>
                Обновить профиль
              </button>
              <button type="button" className="secondary-btn" onClick={openBotDialog}>
                Открыть диалог
              </button>
            </div>
          </section>

          {showAssistant && (
            <section className={`assistant-panel ${profileTheme.tone}`}>
              <div className="assistant-heading">
                <div>
                  <span className="assistant-label">Sber Risk Assistant</span>
                  <h3>Профиль клиента</h3>
                  <p>Здесь отображается только информация о пользователе и клиенте.</p>
                </div>
                <div className={`risk-pill risk-pill-${riskAnalysis?.risk_level ?? 'forgot'}`}>
                  <span className="risk-pill-caption">Уровень риска</span>
                  <strong>{riskAnalysis ? scenarioLabels[riskAnalysis.risk_level] : 'н/д'}</strong>
                </div>
              </div>

              <div className="insights-grid assistant-insights-grid">
                <article className="insight-card">
                  <span className="insight-label">Профиль клиента</span>
                  {clientProfile ? (
                    <dl className="detail-list">
                      <div>
                        <dt>Клиент</dt>
                        <dd>{clientProfile.full_name}</dd>
                      </div>
                      <div>
                        <dt>Доход</dt>
                        <dd>{formatMoney(clientProfile.data.monthly_income)}</dd>
                      </div>
                      <div>
                        <dt>Платёж</dt>
                        <dd>{formatMoney(clientProfile.data.monthly_payment)}</dd>
                      </div>
                      <div>
                        <dt>Сумма кредита</dt>
                        <dd>{formatMoney(clientProfile.data.approved_amount ?? 0)}</dd>
                      </div>
                      <div>
                        <dt>Просрочка</dt>
                        <dd>{clientProfile.data.total_overdue_days} дней</dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="empty-copy">Профиль ещё не загружен.</p>
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

      {isBotDialogOpen && (
        <div className="dialog-backdrop" role="presentation" onClick={closeBotDialog}>
          <section
            className="dialog-window"
            role="dialog"
            aria-modal="true"
            aria-labelledby="assistant-dialog-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="dialog-header">
              <div>
                <span className="section-label">Диалог</span>
                <h3 id="assistant-dialog-title">
                  {clientProfile?.retention_dialog_enabled && riskAnalysis
                    ? `Поддержка для сценария ${scenarioLabels[riskAnalysis.risk_level]?.toLowerCase()}`
                    : 'Диалог с ботом'}
                </h3>
              </div>
              <button type="button" className="icon-btn dialog-close" onClick={closeBotDialog} aria-label="Закрыть диалог">
                ×
              </button>
            </div>

            <div className="retention-layout dialog-layout">
              <div className="retention-chat">
                {clientProfile?.retention_dialog_enabled && riskAnalysis ? (
                  retentionMessages.map((message, index) => (
                    <article
                      key={`${message.content}-${index}`}
                      className={`retention-message retention-message-${message.type}`}
                    >
                      <p>{message.content}</p>
                    </article>
                  ))
                ) : (
                  <article className="retention-message retention-message-bot">
                    <p>Для этого клиента отдельный сценарий сопровождения сейчас не требуется.</p>
                  </article>
                )}
              </div>

              <div className="retention-side">
                <p className="assistant-note">
                  {clientProfile?.retention_dialog_enabled
                    ? clientProfile.retention_summary
                    : 'Дополнительный диалог будет доступен только при необходимости сопровождения.'}
                </p>

                {clientProfile?.retention_dialog_enabled && (
                  <>
                    <div className="retention-quick-replies">
                      {clientProfile.retention_quick_replies.map((item) => (
                        <button key={item} type="button" className="ghost-chip" onClick={() => handleRetentionSubmit(item)}>
                          {item}
                        </button>
                      ))}
                    </div>
                    <div className="retention-form">
                      <textarea
                        value={retentionInput}
                        onChange={(event) => setRetentionInput(event.target.value)}
                        rows={4}
                        placeholder="Введите сообщение"
                      />
                      <button
                        type="button"
                        className="primary-btn retention-submit"
                        onClick={() => handleRetentionSubmit()}
                        disabled={!retentionInput.trim() || isRetentionLoading}
                      >
                        {isRetentionLoading ? 'Отправляем...' : 'Отправить'}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
