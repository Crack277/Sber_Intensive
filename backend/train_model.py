from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / 'bank_clients_synthetic_realistic.csv'
MODEL_PATH = BASE_DIR / 'risk_model.pkl'
METADATA_PATH = BASE_DIR / 'risk_model_metadata.json'

RANDOM_STATE = 42
RISK_GROUPS = ['forgot', 'worried', 'bankruptcy']


@dataclass
class CandidateResult:
    name: str
    params: dict
    validation_accuracy: float
    validation_macro_f1: float


def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f'Не найден датасет: {DATA_PATH}')

    df = pd.read_csv(DATA_PATH)
    print(f'Загружен датасет: {df.shape}')
    return df


def build_risk_labels(df: pd.DataFrame) -> pd.Series:
    cluster_features = [
        'num_credit_contracts',
        'num_closed_loans',
        'total_overdue_days',
        'max_overdue_days',
        'num_past_delinquencies',
        'has_bankruptcy',
        'dti_ratio',
        'payment_to_income_ratio',
        'loan_rate',
        'monthly_income',
        'total_expenses',
        'avg_monthly_turnover',
        'living_area_sqm',
        'children_count',
        'avg_transaction_amount',
        'num_transactions_monthly',
        'work_experience_total_years',
        'car_value',
        'real_estate_count',
        'tenure_months',
    ]

    available_cluster_features = [column for column in cluster_features if column in df.columns]
    cluster_frame = df[available_cluster_features].copy().fillna(0)

    scaler = StandardScaler()
    cluster_values = scaler.fit_transform(cluster_frame)

    kmeans = KMeans(n_clusters=3, random_state=RANDOM_STATE, n_init=30)
    cluster_ids = kmeans.fit_predict(cluster_values)

    clustered = cluster_frame.copy()
    clustered['cluster_id'] = cluster_ids
    cluster_stats = clustered.groupby('cluster_id')[available_cluster_features].mean()

    cluster_scores: dict[int, float] = {}
    for cluster_id in cluster_stats.index:
        stats = cluster_stats.loc[cluster_id]
        cluster_scores[int(cluster_id)] = (
            stats.get('total_overdue_days', 0) * 0.35
            + stats.get('max_overdue_days', 0) * 0.15
            + stats.get('num_past_delinquencies', 0) * 18
            + stats.get('has_bankruptcy', 0) * 120
            + stats.get('dti_ratio', 0) * 45
            + stats.get('payment_to_income_ratio', 0) * 35
            + stats.get('loan_rate', 0) * 0.8
            - stats.get('monthly_income', 0) / 15000
            - stats.get('avg_monthly_turnover', 0) / 80000
        )

    sorted_clusters = sorted(cluster_scores.items(), key=lambda item: item[1])
    mapping = {cluster_id: RISK_GROUPS[idx] for idx, (cluster_id, _) in enumerate(sorted_clusters)}

    print('\nКластеры и риск-скор:')
    for cluster_id, score in sorted_clusters:
        print(f'  cluster {cluster_id}: {mapping[cluster_id]} ({score:.2f})')

    return pd.Series(cluster_ids, index=df.index).map(mapping)


def prepare_features(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    prepared = pd.DataFrame(index=frame.index)

    categorical_columns = [
        'marital_status',
        'income_source',
        'premium_category',
        'employment_type',
        'employer_industry',
        'position_level',
        'loan_purpose',
        'collateral_type',
        'client_segment',
    ]

    numeric_columns = [
        'living_area_sqm',
        'children_count',
        'monthly_income',
        'total_expenses',
        'dti_ratio',
        'avg_monthly_turnover',
        'has_credit_card',
        'num_credit_contracts',
        'num_closed_loans',
        'total_overdue_days',
        'max_overdue_days',
        'num_past_delinquencies',
        'has_bankruptcy',
        'avg_transaction_amount',
        'num_transactions_monthly',
        'uses_mobile_banking',
        'uses_investment_products',
        'has_autopayment',
        'work_experience_total_years',
        'has_business',
        'business_profit',
        'owns_car',
        'car_value',
        'owns_real_estate',
        'real_estate_count',
        'owns_land',
        'requested_amount',
        'approved_amount',
        'loan_rate',
        'monthly_payment',
        'payment_to_income_ratio',
        'has_guarantor',
        'has_higher_education',
        'is_salary_client',
        'is_premium_client',
        'tenure_months',
    ]

    for column in numeric_columns:
        if column in frame.columns:
            prepared[column] = pd.to_numeric(frame[column], errors='coerce').fillna(0)

    engineered_features = {
        'debt_to_income': prepared.get('monthly_payment', 0) / (prepared.get('monthly_income', 0) + 1),
        'overdue_ratio': prepared.get('total_overdue_days', 0) / (prepared.get('tenure_months', 0) + 1),
        'loan_success_rate': prepared.get('approved_amount', 0) / (prepared.get('requested_amount', 0) + 1),
        'credit_utilization': prepared.get('num_credit_contracts', 0) / (prepared.get('num_closed_loans', 0) + 1),
        'payment_burden': prepared.get('monthly_payment', 0) / (prepared.get('total_expenses', 0) + 1),
        'expense_to_income': prepared.get('total_expenses', 0) / (prepared.get('monthly_income', 0) + 1),
        'overdue_severity': prepared.get('max_overdue_days', 0) / (prepared.get('total_overdue_days', 0) + 1),
    }

    for feature_name, values in engineered_features.items():
        prepared[feature_name] = pd.Series(values, index=prepared.index).replace([np.inf, -np.inf], 0).fillna(0)

    for column in categorical_columns:
        if column in frame.columns:
            dummies = pd.get_dummies(frame[column].fillna('missing'), prefix=column, dummy_na=False)
            prepared = pd.concat([prepared, dummies], axis=1)

    prepared = prepared.replace([np.inf, -np.inf], 0).fillna(0)
    return prepared


def candidate_models() -> list[tuple[str, MLPClassifier]]:
    return [
        (
            'mlp_balanced',
            MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0005,
                batch_size=32,
                learning_rate_init=0.001,
                max_iter=800,
                early_stopping=True,
                validation_fraction=0.15,
                random_state=RANDOM_STATE,
            ),
        ),
        (
            'mlp_wide',
            MLPClassifier(
                hidden_layer_sizes=(256, 128, 64),
                activation='relu',
                solver='adam',
                alpha=0.001,
                batch_size=32,
                learning_rate_init=0.0007,
                max_iter=1000,
                early_stopping=True,
                validation_fraction=0.15,
                random_state=RANDOM_STATE,
            ),
        ),
        (
            'mlp_deep_regularized',
            MLPClassifier(
                hidden_layer_sizes=(256, 128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.003,
                batch_size=64,
                learning_rate_init=0.0008,
                max_iter=1200,
                early_stopping=True,
                validation_fraction=0.15,
                random_state=RANDOM_STATE,
            ),
        ),
    ]


def select_best_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
) -> tuple[str, MLPClassifier, list[CandidateResult]]:
    results: list[CandidateResult] = []
    best_name = ''
    best_model: MLPClassifier | None = None
    best_score = -1.0

    for name, model in candidate_models():
        model.fit(x_train, y_train)
        predictions = model.predict(x_val)
        accuracy = accuracy_score(y_val, predictions)
        macro_f1 = f1_score(y_val, predictions, average='macro')

        results.append(
            CandidateResult(
                name=name,
                params=model.get_params(),
                validation_accuracy=float(accuracy),
                validation_macro_f1=float(macro_f1),
            )
        )
        print(f'{name}: val_accuracy={accuracy:.4f}, val_macro_f1={macro_f1:.4f}')

        if macro_f1 > best_score:
            best_name = name
            best_model = model
            best_score = macro_f1

    if best_model is None:
        raise RuntimeError('Не удалось выбрать модель.')

    return best_name, best_model, results


def main() -> None:
    df = load_dataset()
    risk_labels = build_risk_labels(df)
    features = prepare_features(df)

    common_index = features.index.intersection(risk_labels.dropna().index)
    features = features.loc[common_index]
    risk_labels = risk_labels.loc[common_index]

    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(risk_labels)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    x_train_full, x_test, y_train_full, y_test = train_test_split(
        scaled_features,
        encoded_labels,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=encoded_labels,
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_train_full,
        y_train_full,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_train_full,
    )

    print(f'\nРазмер train: {x_train.shape[0]}')
    print(f'Размер validation: {x_val.shape[0]}')
    print(f'Размер test: {x_test.shape[0]}')
    print(f'Количество признаков: {features.shape[1]}')

    best_name, _, search_results = select_best_model(x_train, y_train, x_val, y_val)
    best_params = next(item.params for item in search_results if item.name == best_name)

    base_model = MLPClassifier(**best_params)
    base_model.fit(x_train, y_train)

    calibrated_model = CalibratedClassifierCV(FrozenEstimator(base_model), method='sigmoid', cv=None)
    calibrated_model.fit(x_val, y_val)

    train_predictions = calibrated_model.predict(x_train_full)
    test_predictions = calibrated_model.predict(x_test)

    train_accuracy = accuracy_score(y_train_full, train_predictions)
    test_accuracy = accuracy_score(y_test, test_predictions)
    test_macro_f1 = f1_score(y_test, test_predictions, average='macro')
    test_probabilities = calibrated_model.predict_proba(x_test).max(axis=1)

    print('\nИтоговое качество:')
    print(f'  train_accuracy={train_accuracy:.4f}')
    print(f'  test_accuracy={test_accuracy:.4f}')
    print(f'  test_macro_f1={test_macro_f1:.4f}')
    print(
        '  test_confidence_quantiles='
        f'{{p10: {np.quantile(test_probabilities, 0.10):.4f}, '
        f'p50: {np.quantile(test_probabilities, 0.50):.4f}, '
        f'p90: {np.quantile(test_probabilities, 0.90):.4f}}}'
    )
    print('\nClassification report:')
    print(classification_report(y_test, test_predictions, target_names=label_encoder.classes_))
    print('Confusion matrix:')
    print(confusion_matrix(y_test, test_predictions))

    model_bundle = {
        'model': calibrated_model,
        'scaler': scaler,
        'label_encoder': label_encoder,
        'feature_columns': features.columns.tolist(),
    }
    joblib.dump(model_bundle, MODEL_PATH)

    metadata = {
        'model_type': 'CalibratedClassifierCV',
        'base_model_type': 'MLPClassifier',
        'selected_candidate': best_name,
        'train_accuracy': float(train_accuracy),
        'test_accuracy': float(test_accuracy),
        'test_macro_f1': float(test_macro_f1),
        'test_confidence_p10': float(np.quantile(test_probabilities, 0.10)),
        'test_confidence_p50': float(np.quantile(test_probabilities, 0.50)),
        'test_confidence_p90': float(np.quantile(test_probabilities, 0.90)),
        'classes': label_encoder.classes_.tolist(),
        'feature_count': int(features.shape[1]),
        'dataset_size': int(len(features)),
        'train_size': int(x_train_full.shape[0]),
        'test_size': int(x_test.shape[0]),
        'trained_at': datetime.now().isoformat(timespec='seconds'),
        'candidate_results': [asdict(item) for item in search_results],
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'\nСохранена модель: {MODEL_PATH}')
    print(f'Сохранены метаданные: {METADATA_PATH}')


if __name__ == '__main__':
    main()
