import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import joblib
import os
import json
import pickle
from datetime import datetime

warnings.filterwarnings('ignore')

# ===== ЗАГРУЗКА ДАННЫХ =====
print("=" * 60)
print("ЗАГРУЗКА ДАННЫХ")
print("=" * 60)

# Проверяем наличие файла
file_path = 'bank_clients_filtered.csv'
if not os.path.exists(file_path):
    print(f"❌ Файл {file_path} не найден!")
    print("Создаю синтетический датасет для демонстрации...")

    # Создаем синтетический датасет
    np.random.seed(42)
    n_samples = 5000

    df = pd.DataFrame({
        # Демографические
        'marital_status': np.random.choice(['женат', 'холост', 'разведен', 'вдовец'], n_samples),
        'living_area_sqm': np.random.normal(60, 20, n_samples).clip(20, 200),
        'children_count': np.random.poisson(1, n_samples).clip(0, 5),

        # Финансовые
        'monthly_income': np.random.lognormal(10.5, 0.8, n_samples).clip(15000, 500000),
        'income_source': np.random.choice(['зарплата', 'самозанятый', 'бизнес', 'пенсия'], n_samples,
                                          p=[0.6, 0.2, 0.1, 0.1]),
        'total_expenses': np.random.lognormal(10, 0.7, n_samples).clip(10000, 300000),
        'dti_ratio': np.random.beta(2, 5, n_samples).clip(0, 1),
        'avg_monthly_turnover': np.random.lognormal(11, 0.9, n_samples).clip(20000, 1000000),
        'has_credit_card': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),

        # Кредитная история
        'num_credit_contracts': np.random.poisson(2, n_samples).clip(0, 10),
        'num_closed_loans': np.random.poisson(1.5, n_samples).clip(0, 8),
        'total_overdue_days': np.random.exponential(15, n_samples).clip(0, 365),
        'max_overdue_days': np.random.exponential(10, n_samples).clip(0, 180),
        'num_past_delinquencies': np.random.poisson(1, n_samples).clip(0, 10),
        'has_bankruptcy': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),

        # Поведенческие
        'avg_transaction_amount': np.random.lognormal(8, 1, n_samples).clip(100, 50000),
        'num_transactions_monthly': np.random.poisson(15, n_samples).clip(0, 100),
        'premium_category': np.random.choice(['путешествия', 'рестораны', 'товары', 'ЖКХ'], n_samples),
        'uses_mobile_banking': np.random.choice([0, 1], n_samples, p=[0.1, 0.9]),
        'uses_investment_products': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'has_autopayment': np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),

        # Рабочие
        'employment_type': np.random.choice(['госслужащий', 'частный сектор', 'ИП', 'самозанятый'], n_samples),
        'employer_industry': np.random.choice(['IT', 'производство', 'медицина', 'образование'], n_samples),
        'position_level': np.random.choice(['специалист', 'руководитель', 'топ-менеджер'], n_samples,
                                           p=[0.7, 0.25, 0.05]),
        'work_experience_total_years': np.random.gamma(10, 1, n_samples).clip(0, 40),
        'has_business': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'business_profit': np.random.lognormal(11, 1.5, n_samples) * np.random.choice([0, 1], n_samples,
                                                                                      p=[0.85, 0.15]),

        # Имущественные
        'owns_car': np.random.choice([0, 1], n_samples, p=[0.4, 0.6]),
        'car_value': np.random.lognormal(12, 1, n_samples) * np.random.choice([0, 1], n_samples, p=[0.4, 0.6]),
        'owns_real_estate': np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),
        'real_estate_count': np.random.poisson(0.5, n_samples).clip(0, 5),
        'owns_land': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),

        # Кредитные
        'loan_purpose': np.random.choice(['ремонт', 'авто', 'обучение', 'рефинансирование', 'неотложные нужды'],
                                         n_samples),
        'requested_amount': np.random.lognormal(12, 0.8, n_samples).clip(50000, 3000000),
        'approved_amount': np.random.lognormal(12, 0.8, n_samples) * np.random.uniform(0.5, 1, n_samples),
        'loan_rate': np.random.uniform(10, 35, n_samples),
        'monthly_payment': np.random.lognormal(9, 0.7, n_samples).clip(5000, 100000),
        'payment_to_income_ratio': np.random.beta(2, 5, n_samples).clip(0, 1),
        'collateral_type': np.random.choice(['недвижимость', 'авто', 'поручитель', 'без обеспечения'], n_samples),
        'has_guarantor': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),

        # Социальные
        'has_higher_education': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),

        # Маркетинговые
        'is_salary_client': np.random.choice([0, 1], n_samples, p=[0.4, 0.6]),
        'is_premium_client': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'client_segment': np.random.choice(['массовый', 'масс-премиум', 'приват', 'премиум'], n_samples,
                                           p=[0.6, 0.25, 0.1, 0.05]),
        'tenure_months': np.random.poisson(24, n_samples).clip(1, 120),
    })

    # Корректируем некоторые поля
    df['approved_amount'] = df['approved_amount'].clip(0, df['requested_amount'])
    df['total_expenses'] = df['total_expenses'].clip(0, df['monthly_income'] * 0.9)

    print(f"✅ Создан синтетический датасет: {df.shape}")
else:
    df = pd.read_csv(file_path)
    print(f"✅ Загружен датасет: {df.shape}")

# ===== СПИСОК ВСЕХ ПОЛЕЙ ДЛЯ АНАЛИЗА =====
all_fields = [
    # 1. Демографические и личные данные
    'marital_status', 'living_area_sqm', 'children_count',
    # 2. Финансовые и доходные
    'monthly_income', 'income_source', 'total_expenses', 'dti_ratio',
    'avg_monthly_turnover', 'has_credit_card',
    # 3. Кредитная история
    'num_credit_contracts', 'num_closed_loans', 'total_overdue_days',
    'max_overdue_days', 'num_past_delinquencies', 'has_bankruptcy',
    # 4. Поведенческие и транзакционные
    'avg_transaction_amount', 'num_transactions_monthly', 'premium_category',
    'uses_mobile_banking', 'uses_investment_products', 'has_autopayment',
    # 5. Рабочие и профессиональные
    'employment_type', 'employer_industry', 'position_level',
    'work_experience_total_years', 'has_business', 'business_profit',
    # 6. Имущественные
    'owns_car', 'car_value', 'owns_real_estate', 'real_estate_count', 'owns_land',
    # 7. Кредитные (для конкретной заявки)
    'loan_purpose', 'requested_amount', 'approved_amount', 'loan_rate',
    'monthly_payment', 'payment_to_income_ratio', 'collateral_type', 'has_guarantor',
    # 9. Социальные и демографические
    'has_higher_education',
    # 10. Маркетинговые и продуктовые
    'is_salary_client', 'is_premium_client', 'client_segment', 'tenure_months'
]

# Проверяем наличие полей в датасете
available_fields = [col for col in all_fields if col in df.columns]
missing_fields = [col for col in all_fields if col not in df.columns]

if missing_fields:
    print(f"\n⚠️ Отсутствующие поля в датасете ({len(missing_fields)}):")
    for field in missing_fields[:10]:
        print(f"  - {field}")
    if len(missing_fields) > 10:
        print(f"  ... и еще {len(missing_fields) - 10}")

print(f"\n✅ Доступно полей: {len(available_fields)} из {len(all_fields)}")

# ===== 1. ПРИЗНАКИ ДЛЯ КЛАСТЕРИЗАЦИИ =====
features_for_clustering = [
    'num_credit_contracts', 'num_closed_loans', 'total_overdue_days',
    'max_overdue_days', 'num_past_delinquencies', 'has_bankruptcy',
    'dti_ratio', 'payment_to_income_ratio', 'loan_rate',
    'monthly_income', 'total_expenses', 'avg_monthly_turnover',
    'living_area_sqm', 'children_count', 'avg_transaction_amount',
    'num_transactions_monthly', 'work_experience_total_years',
    'car_value', 'real_estate_count', 'tenure_months'
]

# Оставляем только доступные числовые признаки
features_for_clustering = [f for f in features_for_clustering if f in df.columns]

# Удаляем строки с пропусками в признаках кластеризации
df_clean = df[features_for_clustering].dropna()

# Преобразуем бинарные признаки в int
binary_cols = ['has_bankruptcy']
for col in binary_cols:
    if col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(int)

# Нормализация
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_clean)

# ===== 2. КЛАСТЕРИЗАЦИЯ НА 3 ГРУППЫ =====
print("\n" + "=" * 60)
print("КЛАСТЕРИЗАЦИЯ")
print("=" * 60)

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)

df_clustered = df_clean.copy()
df_clustered['Cluster'] = clusters

print("\nХАРАКТЕРИСТИКИ КЛАСТЕРОВ")
print("-" * 40)
cluster_stats = df_clustered.groupby('Cluster')[features_for_clustering].mean()
print(cluster_stats.round(2))

# ===== 3. ИНТЕРПРЕТАЦИЯ КЛАСТЕРОВ =====
print("\n" + "=" * 60)
print("ИНТЕРПРЕТАЦИЯ КЛАСТЕРОВ")
print("=" * 60)

# Рассчитываем риск-скор для каждого кластера
cluster_scores = {}
for cluster in range(3):
    stats = cluster_stats.loc[cluster]
    risk_score = (
            stats.get('total_overdue_days', 0) * 0.3 +
            stats.get('num_past_delinquencies', 0) * 15 +
            stats.get('has_bankruptcy', 0) * 100 +
            stats.get('dti_ratio', 0) * 40 +
            stats.get('payment_to_income_ratio', 0) * 30
    )
    cluster_scores[cluster] = risk_score

# Сортируем по риску
sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1])

# Четкое разделение на 3 группы
group_mapping = {}
group_names = ['forgot', 'worried', 'bankruptcy']

for i, (cluster, score) in enumerate(sorted_clusters):
    group_mapping[cluster] = group_names[i]
    stats = cluster_stats.loc[cluster]
    print(f"\nКластер {cluster} -> {group_names[i].upper()} (риск-скор: {score:.0f})")
    print(f"  📊 Просрочка: {stats.get('total_overdue_days', 0):.1f} дней")
    print(f"  📊 Макс просрочка: {stats.get('max_overdue_days', 0):.1f} дней")
    print(f"  📊 Кол-во просрочек: {stats.get('num_past_delinquencies', 0):.2f}")
    print(f"  📊 Банкротство: {stats.get('has_bankruptcy', 0) * 100:.1f}%")
    print(f"  📊 DTI: {stats.get('dti_ratio', 0):.2f}")
    print(f"  📊 Платеж/доход: {stats.get('payment_to_income_ratio', 0):.2f}")

df_clustered['Risk_Label'] = df_clustered['Cluster'].map(group_mapping)

print("\n" + "=" * 60)
print("РАСПРЕДЕЛЕНИЕ ПО ГРУППАМ")
print("=" * 60)
distribution = df_clustered['Risk_Label'].value_counts()
print(distribution)
print(f"\nПроценты:\n{distribution / len(df_clustered) * 100:.1f}%")

# ===== 4. ПОДГОТОВКА ПРИЗНАКОВ ДЛЯ НЕЙРОСЕТИ =====
print("\n" + "=" * 60)
print("ПОДГОТОВКА ДАННЫХ ДЛЯ НЕЙРОННОЙ СЕТИ")
print("=" * 60)


def prepare_features_for_nn(data, available_fields):
    df_prepared = pd.DataFrame(index=data.index)

    # Категориальные признаки для one-hot encoding
    categorical_cols = [
        'marital_status', 'income_source', 'premium_category',
        'employment_type', 'employer_industry', 'position_level',
        'loan_purpose', 'collateral_type', 'client_segment'
    ]

    # Числовые признаки
    numeric_cols = [
        'living_area_sqm', 'children_count', 'monthly_income', 'total_expenses',
        'dti_ratio', 'avg_monthly_turnover', 'has_credit_card',
        'num_credit_contracts', 'num_closed_loans', 'total_overdue_days',
        'max_overdue_days', 'num_past_delinquencies', 'has_bankruptcy',
        'avg_transaction_amount', 'num_transactions_monthly',
        'uses_mobile_banking', 'uses_investment_products', 'has_autopayment',
        'work_experience_total_years', 'has_business', 'business_profit',
        'owns_car', 'car_value', 'owns_real_estate', 'real_estate_count', 'owns_land',
        'requested_amount', 'approved_amount', 'loan_rate', 'monthly_payment',
        'payment_to_income_ratio', 'has_guarantor', 'has_higher_education',
        'is_salary_client', 'is_premium_client', 'tenure_months'
    ]

    # Создаем дополнительные признаки
    if 'monthly_payment' in data.columns and 'monthly_income' in data.columns:
        data['debt_to_income'] = data['monthly_payment'] / (data['monthly_income'] + 1)
        numeric_cols.append('debt_to_income')

    if 'total_overdue_days' in data.columns and 'tenure_months' in data.columns:
        data['overdue_ratio'] = data['total_overdue_days'] / (data['tenure_months'] + 1)
        numeric_cols.append('overdue_ratio')

    if 'approved_amount' in data.columns and 'requested_amount' in data.columns:
        data['loan_success_rate'] = data['approved_amount'] / (data['requested_amount'] + 1)
        numeric_cols.append('loan_success_rate')

    if 'num_credit_contracts' in data.columns and 'num_closed_loans' in data.columns:
        data['credit_utilization'] = data['num_credit_contracts'] / (data['num_closed_loans'] + 1)
        numeric_cols.append('credit_utilization')

    if 'monthly_payment' in data.columns and 'total_expenses' in data.columns:
        data['payment_burden'] = data['monthly_payment'] / (data['total_expenses'] + 1)
        numeric_cols.append('payment_burden')

    # Добавляем числовые признаки
    for col in numeric_cols:
        if col in data.columns:
            df_prepared[col] = data[col].fillna(0)

    # One-hot encoding для категориальных признаков
    for col in categorical_cols:
        if col in data.columns:
            dummies = pd.get_dummies(data[col], prefix=col, dummy_na=True)
            df_prepared = pd.concat([df_prepared, dummies], axis=1)

    return df_prepared


# Подготавливаем все данные
df_nn = prepare_features_for_nn(df, available_fields)
print(f"Используем {df_nn.shape[1]} признаков после one-hot encoding")

# Получаем метки
common_index = df_nn.index.intersection(df_clustered.index)
df_nn = df_nn.loc[common_index]
y_labels = df_clustered.loc[common_index, 'Risk_Label']

# Кодируем целевую переменную
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_labels)
print(f"\nЦелевые классы: {dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}")

# Нормализуем
scaler_nn = StandardScaler()
X_scaled_nn = scaler_nn.fit_transform(df_nn)

# Разделяем с сохранением пропорций
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled_nn, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Обучающая выборка: {X_train.shape[0]}")
print(f"Тестовая выборка: {X_test.shape[0]}")

# ===== 5. ОБУЧЕНИЕ НЕЙРОННОЙ СЕТИ =====
print("\n" + "=" * 60)
print("ОБУЧЕНИЕ НЕЙРОННОЙ СЕТИ")
print("=" * 60)

mlp = MLPClassifier(
    hidden_layer_sizes=(256, 128, 64, 32),
    activation='relu',
    solver='adam',
    alpha=0.001,
    batch_size=32,
    max_iter=1000,
    random_state=42,
    early_stopping=True,
    validation_fraction=0.15,
    verbose=True
)

print("Начало обучения...")
mlp.fit(X_train, y_train)

# ===== 6. ОЦЕНКА МОДЕЛИ =====
y_pred = mlp.predict(X_test)
y_pred_train = mlp.predict(X_train)

print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ ОБУЧЕНИЯ")
print("=" * 60)
print(f"\n✅ Точность на обучении: {accuracy_score(y_train, y_pred_train) * 100:.2f}%")
print(f"✅ Точность на тесте: {accuracy_score(y_test, y_pred) * 100:.2f}%")

print("\n" + "=" * 60)
print("ДЕТАЛЬНЫЙ ОТЧЕТ")
print("=" * 60)
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# ===== 7. ВИЗУАЛИЗАЦИЯ =====
print("\n" + "=" * 60)
print("СОЗДАНИЕ ВИЗУАЛИЗАЦИЙ")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Матрица ошибок
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0],
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_)
axes[0, 0].set_title('Матрица ошибок')
axes[0, 0].set_xlabel('Предсказано')
axes[0, 0].set_ylabel('Истинное значение')

# Распределение
dist = df_clustered['Risk_Label'].value_counts()
colors = {'forgot': 'green', 'worried': 'orange', 'bankruptcy': 'red'}
bars = axes[0, 1].bar(range(len(dist)), dist.values,
                      color=[colors.get(x, 'blue') for x in dist.index])
axes[0, 1].set_title('Распределение клиентов')
axes[0, 1].set_xlabel('Группа')
axes[0, 1].set_ylabel('Количество')
axes[0, 1].set_xticks(range(len(dist)))
axes[0, 1].set_xticklabels(dist.index)

# Сравнение ключевых признаков
risk_comparison = df_clustered.groupby('Risk_Label')[
    ['total_overdue_days', 'dti_ratio', 'loan_rate', 'monthly_income']
].mean()
risk_comparison.plot(kind='bar', ax=axes[1, 0])
axes[1, 0].set_title('Сравнение групп по ключевым признакам')
axes[1, 0].set_xlabel('Группа риска')
axes[1, 0].set_ylabel('Среднее значение')
axes[1, 0].tick_params(axis='x', rotation=0)

# Важность признаков
rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
rf.fit(X_train, y_train)
importances = pd.Series(rf.feature_importances_, index=df_nn.columns)
top_features = importances.nlargest(10)
top_features.plot(kind='barh', ax=axes[1, 1])
axes[1, 1].set_title('Топ-10 важных признаков')
axes[1, 1].set_xlabel('Важность')

plt.tight_layout()
plt.savefig('model_analysis.png', dpi=150)
print("✅ Визуализация сохранена: model_analysis.png")
plt.show()

# ===== 8. СОХРАНЕНИЕ МОДЕЛИ =====
print("\n" + "=" * 60)
print("СОХРАНЕНИЕ МОДЕЛИ")
print("=" * 60)

# Создаем директорию для моделей
models_dir = "models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)
    print(f"✅ Создана директория: {models_dir}/")

# Сохраняем нейронную сеть
model_path = os.path.join(models_dir, "risk_model.joblib")
joblib.dump(mlp, model_path)
print(f"✅ Модель сохранена: {model_path}")

# Сохраняем scaler
scaler_path = os.path.join(models_dir, "scaler.joblib")
joblib.dump(scaler_nn, scaler_path)
print(f"✅ Scaler сохранен: {scaler_path}")

# Сохраняем label encoder
encoder_path = os.path.join(models_dir, "label_encoder.joblib")
joblib.dump(label_encoder, encoder_path)
print(f"✅ Label encoder сохранен: {encoder_path}")

# Сохраняем список колонок
columns_path = os.path.join(models_dir, "feature_columns.joblib")
joblib.dump(df_nn.columns.tolist(), columns_path)
print(f"✅ Список признаков сохранен: {columns_path}")

# Сохраняем список доступных полей
available_fields_path = os.path.join(models_dir, "available_fields.joblib")
joblib.dump(available_fields, available_fields_path)
print(f"✅ Доступные поля сохранены: {available_fields_path}")

# Сохраняем метаинформацию
metadata = {
    "model_type": "MLPClassifier",
    "hidden_layers": [256, 128, 64, 32],
    "activation": "relu",
    "solver": "adam",
    "accuracy_train": float(accuracy_score(y_train, y_pred_train)),
    "accuracy_test": float(accuracy_score(y_test, y_pred)),
    "n_features": df_nn.shape[1],
    "n_classes": len(label_encoder.classes_),
    "classes": label_encoder.classes_.tolist(),
    "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "dataset_size": len(df_clean),
    "train_size": X_train.shape[0],
    "test_size": X_test.shape[0]
}

metadata_path = os.path.join(models_dir, "model_metadata.json")
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=4, ensure_ascii=False)
print(f"✅ Метаданные сохранены: {metadata_path}")

print("\n" + "=" * 60)
print("✅ ВСЕ ОБЪЕКТЫ УСПЕШНО СОХРАНЕНЫ!")
print("=" * 60)
print(f"\n📁 Файлы в директории: {models_dir}/")
for f in os.listdir(models_dir):
    size = os.path.getsize(os.path.join(models_dir, f))
    print(f"   - {f:<30} ({size / 1024:.1f} KB)")

print("\n" + "=" * 60)
print("ИНФОРМАЦИЯ О МОДЕЛИ")
print("=" * 60)
for key, value in metadata.items():
    print(f"  {key}: {value}")

print("\n✅ Обучение завершено! Модель готова к использованию.")