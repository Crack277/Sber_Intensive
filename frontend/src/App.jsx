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

const DEBT_PAYMENT_LINK = '#debt-payment';
const SOLUTIONS_LINK = '#solutions';

const chatOptionSets = {
  root: [
    { id: 'forgot', label: 'Забыл' },
    { id: 'illness', label: 'Заболел' },
    { id: 'money', label: 'Нехватка денег' },
    { id: 'bankruptcy', label: 'Начал процедуру банкротства' },
    { id: 'other', label: 'Другое' },
  ],
  illness: [
    { id: 'short_term', label: 'Краткосрочная' },
    { id: 'long_term', label: 'Долгосрочная' },
    { id: 'unclear', label: 'Пока не понимаю' },
  ],
  money: [
    { id: 'pause', label: 'Взять паузу' },
    { id: 'review', label: 'Пересмотреть условия' },
    { id: 'service_swap', label: 'Обмен долга на услуги' },
  ],
  unclear: [
    { id: 'pause', label: 'Взять паузу' },
    { id: 'specialist', label: 'Связаться со специалистом' },
  ],
  medical_offer: [
    { id: 'thumbs_up', label: 'Палец вверх' },
    { id: 'thumbs_down', label: 'Палец вниз' },
  ],
};

function createChatMessage(type, content, extra = {}) {
  return {
    type,
    content,
    ...extra,
  };
}

function getInitialChatMessages(clientName) {
  return [
    createChatMessage(
      'bot',
      `Здравствуйте${clientName ? `, ${clientName}` : ''}! Хочу понять ситуацию, чтобы предложить решение. Может, укажите, что у Вас произошло?`
    ),
  ];
}

function formatMoney(value) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value);
}

function App() {
  const [activeTab, setActiveTab] = useState('main');
  const [showAssistant, setShowAssistant] = useState(true);
  const [isBotDialogOpen, setIsBotDialogOpen] = useState(false);
  const [clientProfile, setClientProfile] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [retentionMessages, setRetentionMessages] = useState([]);
  const [chatOptions, setChatOptions] = useState([]);
  const [retentionInput, setRetentionInput] = useState('');
  const [, setIsLoadingProfile] = useState(false);
  const [isRetentionLoading, setIsRetentionLoading] = useState(false);

  const profileTheme = useMemo(() => {
    const scenario = riskAnalysis?.risk_level ?? 'forgot';
    return scenarioThemes[scenario];
  }, [riskAnalysis]);

  const resetRetentionChat = () => {
    setRetentionMessages(getInitialChatMessages(clientProfile?.full_name));
    setChatOptions(chatOptionSets.root);
    setRetentionInput('');
    setIsRetentionLoading(false);
  };

  const openBotDialog = () => {
    resetRetentionChat();
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
        getInitialChatMessages(payload.full_name)
      );
      setChatOptions(chatOptionSets.root);
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

  const applyChatBranch = (branchId) => {
    switch (branchId) {
      case 'forgot':
        return {
          messages: [
            createChatMessage('bot', 'Вы можете внести свой платёж, перейдя по ссылке сверху.'),
          ],
          options: [],
        };
      case 'illness':
        return {
          messages: [createChatMessage('bot', 'Ситуация, скорее:')],
          options: chatOptionSets.illness,
        };
      case 'money':
        return {
          messages: [
            createChatMessage(
              'bot',
              'Действительно, так бывает. Ситуация не из приятных, но мы можем помочь и предложить следующие варианты:'
            ),
          ],
          options: chatOptionSets.money,
        };
      case 'bankruptcy':
        return {
          messages: [
            createChatMessage('warning', '', {
              title: 'ВНИМАНИЕ!',
              paragraphs: [
                'Банкротство - это не лёгкий путь, а разрушительный шаг. Вы можете потерять имущество, лишиться кредитов и навредить своей репутации, получив "чёрную метку".',
                'Сам процесс очень долгий, эмоционально выматывающий и не гарантирует полного избавления от долгов.',
                'Лучшее решение - остаться с нами.',
              ],
              link: {
                href: SOLUTIONS_LINK,
                label: 'Здесь представлены варианты решения Вашей проблемы.',
              },
              footer:
                'Это поможет сохранить Ваше имущество и восстановить финансовое положение.',
            }),
          ],
          options: [],
        };
      case 'other':
        return {
          messages: [createChatMessage('bot', 'В ближайшее время специалист с Вами свяжется!')],
          options: [],
        };
      case 'unclear':
        return {
          messages: [createChatMessage('bot', 'Давайте выберем безопасный следующий шаг:')],
          options: chatOptionSets.unclear,
        };
      case 'long_term':
        return applyChatBranch('money');
      case 'short_term':
        return {
          messages: [
            createChatMessage(
              'bot',
              'Увы, так бывает. Специально для Вашей проблемы у нас есть выгодное предложение: дополнительная скидка на медицинские услуги и лекарственные препараты. Также, на период лечения, мы можем пересмотреть условия по Вашей задолженности. Как Вам наше предложение?'
            ),
          ],
          options: chatOptionSets.medical_offer,
        };
      case 'pause':
      case 'review':
      case 'service_swap':
      case 'specialist':
      case 'thumbs_up':
        return {
          messages: [createChatMessage('bot', 'В ближайшее время специалист с Вами свяжется!')],
          options: [],
        };
      case 'thumbs_down':
        return {
          messages: [
            createChatMessage('bot', 'У нас есть ещё предложения для Вас. Готовы их с Вами обсудить. Ожидайте звонок от специалиста.'),
          ],
          options: [],
        };
      default:
        return {
          messages: [createChatMessage('bot', 'В ближайшее время специалист с Вами свяжется!')],
          options: [],
        };
    }
  };

  const handleOptionSelect = (option) => {
    const nextBranch = applyChatBranch(option.id);
    setRetentionMessages((prev) => [
      ...prev,
      createChatMessage('user', option.label),
      ...nextBranch.messages,
    ]);
    setChatOptions(nextBranch.options);
  };

  const handleRetentionSubmit = (prefilledMessage) => {
    const message = (prefilledMessage ?? retentionInput).trim();

    if (!message) {
      return;
    }

    setRetentionMessages((prev) => [
      ...prev,
      createChatMessage('user', message),
      createChatMessage('bot', 'В ближайшее время специалист с Вами свяжется!'),
    ]);
    setRetentionInput('');
    setChatOptions([]);
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
                <h3 id="assistant-dialog-title">СберАссистент</h3>
              </div>
              <button type="button" className="icon-btn dialog-close" onClick={closeBotDialog} aria-label="Закрыть диалог">
                ×
              </button>
            </div>

            <div className="chat-support-shell">
              <a className="dialog-payment-link" href={DEBT_PAYMENT_LINK}>
                Перейти к внесению задолженности
              </a>

              <div className="retention-chat retention-chat-single">
                {retentionMessages.map((message, index) => (
                  <article
                    key={`${message.type}-${index}-${message.content}`}
                    className={`retention-message retention-message-${message.type}`}
                  >
                    {message.title && <strong className="retention-warning-title">{message.title}</strong>}
                    {message.content ? <p>{message.content}</p> : null}
                    {message.paragraphs?.map((paragraph) => (
                      <p key={paragraph}>{paragraph}</p>
                    ))}
                    {message.link ? (
                      <a className="dialog-inline-link" href={message.link.href}>
                        {message.link.label}
                      </a>
                    ) : null}
                    {message.footer ? <p>{message.footer}</p> : null}
                  </article>
                ))}
              </div>

              {chatOptions.length > 0 && (
                <div className="retention-quick-replies retention-quick-replies-chat">
                  {chatOptions.map((option) => (
                    <button key={option.id} type="button" className="ghost-chip" onClick={() => handleOptionSelect(option)}>
                      {option.label}
                    </button>
                  ))}
                </div>
              )}

              <div className="retention-form retention-form-chat">
                <textarea
                  value={retentionInput}
                  onChange={(event) => setRetentionInput(event.target.value)}
                  rows={3}
                  placeholder="Введите сообщение..."
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
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
