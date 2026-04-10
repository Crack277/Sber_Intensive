from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / 'bank_clients_synthetic_realistic.csv'
RANDOM_SEED = 42
ROW_COUNT = 12000

MARITAL_STATUSES = ['single', 'married', 'divorced', 'widowed']
INCOME_SOURCES = ['salary', 'self_employed', 'business', 'pension']
PREMIUM_CATEGORIES = ['travel', 'restaurants', 'goods', 'utilities']
EMPLOYMENT_TYPES = ['private', 'public', 'individual_entrepreneur', 'self_employed']
EMPLOYER_INDUSTRIES = ['IT', 'finance', 'manufacturing', 'medicine', 'education', 'retail', 'transport']
POSITION_LEVELS = ['junior', 'specialist', 'manager', 'top_manager']
LOAN_PURPOSES = ['repair', 'car', 'education', 'refinancing', 'consumer', 'mortgage']
COLLATERAL_TYPES = ['none', 'car', 'real_estate', 'guarantor']
CLIENT_SEGMENTS = ['mass', 'mass_premium', 'premium', 'private_banking']


def weighted_choice(rng: np.random.Generator, options: list[str], weights: list[float], size: int) -> np.ndarray:
    normalized = np.asarray(weights, dtype=float)
    normalized = normalized / normalized.sum()
    return rng.choice(options, size=size, p=normalized)


def clip_round(values: np.ndarray, low: float, high: float) -> np.ndarray:
    return np.clip(np.round(values), low, high).astype(int)


def build_dataset(n_rows: int = ROW_COUNT, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = clip_round(rng.normal(41, 11, n_rows), 21, 75)
    marital_status = np.where(
        age < 27,
        weighted_choice(rng, MARITAL_STATUSES, [0.72, 0.22, 0.05, 0.01], n_rows),
        np.where(
            age < 45,
            weighted_choice(rng, MARITAL_STATUSES, [0.22, 0.61, 0.14, 0.03], n_rows),
            weighted_choice(rng, MARITAL_STATUSES, [0.14, 0.58, 0.18, 0.10], n_rows),
        ),
    )

    children_count = np.where(
        marital_status == 'married',
        clip_round(rng.poisson(1.4, n_rows), 0, 4),
        clip_round(rng.poisson(0.4, n_rows), 0, 3),
    )
    has_higher_education = rng.binomial(1, np.clip(0.48 + (age - 25) * 0.004, 0.35, 0.82))

    employment_type = weighted_choice(
        rng,
        EMPLOYMENT_TYPES,
        [0.56, 0.17, 0.12, 0.15],
        n_rows,
    )
    income_source = np.where(
        employment_type == 'public',
        'salary',
        np.where(
            employment_type == 'private',
            weighted_choice(rng, INCOME_SOURCES, [0.88, 0.08, 0.03, 0.01], n_rows),
            np.where(
                employment_type == 'individual_entrepreneur',
                weighted_choice(rng, INCOME_SOURCES, [0.08, 0.18, 0.72, 0.02], n_rows),
                weighted_choice(rng, INCOME_SOURCES, [0.12, 0.77, 0.08, 0.03], n_rows),
            ),
        ),
    )

    employer_industry = weighted_choice(
        rng,
        EMPLOYER_INDUSTRIES,
        [0.18, 0.14, 0.16, 0.10, 0.12, 0.18, 0.12],
        n_rows,
    )

    position_level = np.where(
        age < 27,
        weighted_choice(rng, POSITION_LEVELS, [0.42, 0.50, 0.07, 0.01], n_rows),
        np.where(
            age < 40,
            weighted_choice(rng, POSITION_LEVELS, [0.10, 0.63, 0.23, 0.04], n_rows),
            weighted_choice(rng, POSITION_LEVELS, [0.05, 0.48, 0.34, 0.13], n_rows),
        ),
    )

    work_experience_total_years = np.maximum(age - 21 - rng.integers(0, 8, n_rows), 0)
    work_experience_total_years = clip_round(work_experience_total_years, 0, 45)

    living_area_sqm = np.clip(
        rng.normal(47, 14, n_rows) + children_count * 11 + (marital_status == 'married') * 8,
        18,
        260,
    )

    base_income = (
        42000
        + work_experience_total_years * 2600
        + has_higher_education * 14000
        + np.select(
            [position_level == 'junior', position_level == 'specialist', position_level == 'manager', position_level == 'top_manager'],
            [-10000, 0, 28000, 75000],
            default=0,
        )
        + np.select(
            [employer_industry == 'IT', employer_industry == 'finance', employer_industry == 'medicine', employer_industry == 'education'],
            [30000, 22000, 12000, 5000],
            default=0,
        )
        + np.select(
            [employment_type == 'public', employment_type == 'private', employment_type == 'individual_entrepreneur', employment_type == 'self_employed'],
            [-5000, 0, 18000, 9000],
            default=0,
        )
        + rng.normal(0, 12000, n_rows)
    )
    monthly_income = np.clip(base_income, 18000, 520000)

    is_salary_client = np.where(income_source == 'salary', rng.binomial(1, 0.72, n_rows), rng.binomial(1, 0.18, n_rows))
    uses_mobile_banking = rng.binomial(1, np.clip(0.65 + (age < 55) * 0.20 + (monthly_income > 90000) * 0.06, 0.45, 0.96))
    has_credit_card = rng.binomial(1, np.clip(0.52 + (monthly_income > 70000) * 0.18 + is_salary_client * 0.12, 0.25, 0.93))
    uses_investment_products = rng.binomial(1, np.clip((monthly_income - 70000) / 260000, 0.03, 0.55))
    has_autopayment = rng.binomial(1, np.clip(0.28 + has_credit_card * 0.17 + uses_mobile_banking * 0.19, 0.12, 0.88))

    total_expenses = np.clip(
        monthly_income * rng.uniform(0.38, 0.74, n_rows)
        + children_count * rng.uniform(4000, 12000, n_rows)
        + (marital_status == 'married') * rng.uniform(3000, 9000, n_rows)
        + rng.normal(0, 6000, n_rows),
        12000,
        monthly_income * 0.92,
    )

    avg_monthly_turnover = np.clip(monthly_income * rng.uniform(1.15, 2.8, n_rows) + rng.normal(0, 25000, n_rows), 15000, 1300000)
    num_transactions_monthly = clip_round(rng.normal(24, 9, n_rows) + uses_mobile_banking * 8, 4, 120)
    avg_transaction_amount = np.clip(avg_monthly_turnover / np.maximum(num_transactions_monthly, 1), 150, 120000)

    has_business = np.where(income_source == 'business', rng.binomial(1, 0.88, n_rows), rng.binomial(1, 0.09, n_rows))
    business_profit = np.where(
        has_business == 1,
        np.clip(monthly_income * rng.uniform(0.18, 0.95, n_rows), 10000, 850000),
        0,
    )

    owns_car = rng.binomial(1, np.clip(0.28 + (age > 28) * 0.14 + (monthly_income > 85000) * 0.16, 0.15, 0.86))
    car_value = np.where(owns_car == 1, np.clip(monthly_income * rng.uniform(6, 18, n_rows), 250000, 6500000), 0)

    owns_real_estate = rng.binomial(1, np.clip(0.16 + (age > 30) * 0.16 + (monthly_income > 120000) * 0.19, 0.08, 0.84))
    real_estate_count = np.where(owns_real_estate == 1, clip_round(1 + rng.poisson(0.35, n_rows), 1, 4), 0)
    owns_land = np.where(owns_real_estate == 1, rng.binomial(1, 0.24, n_rows), rng.binomial(1, 0.05, n_rows))

    client_segment = np.select(
        [
            monthly_income < 70000,
            monthly_income < 140000,
            monthly_income < 260000,
        ],
        ['mass', 'mass_premium', 'premium'],
        default='private_banking',
    )
    is_premium_client = np.where(np.isin(client_segment, ['premium', 'private_banking']), 1, 0)

    loan_purpose = weighted_choice(rng, LOAN_PURPOSES, [0.24, 0.17, 0.08, 0.18, 0.25, 0.08], n_rows)
    requested_amount = np.clip(
        monthly_income
        * np.select(
            [
                loan_purpose == 'consumer',
                loan_purpose == 'repair',
                loan_purpose == 'car',
                loan_purpose == 'education',
                loan_purpose == 'refinancing',
                loan_purpose == 'mortgage',
            ],
            [2.8, 3.6, 6.0, 3.2, 4.2, 18.0],
            default=3.5,
        )
        * rng.uniform(0.8, 1.35, n_rows),
        50000,
        8000000,
    )

    risk_pressure = (
        (total_expenses / np.maximum(monthly_income, 1)) * 0.45
        + (children_count * 0.03)
        + (income_source == 'business') * 0.04
        + (employment_type == 'self_employed') * 0.03
        - has_higher_education * 0.03
        - is_salary_client * 0.04
        - owns_real_estate * 0.05
    )
    risk_pressure = np.clip(risk_pressure, 0.05, 0.95)

    num_credit_contracts = clip_round(rng.poisson(1.3 + risk_pressure * 3.2, n_rows), 0, 9)
    num_closed_loans = clip_round(np.maximum(num_credit_contracts - rng.poisson(0.8, n_rows) + rng.integers(0, 3, n_rows), 0), 0, 11)

    loan_rate = np.clip(
        10.5
        + risk_pressure * 18
        + (loan_purpose == 'mortgage') * -3.0
        + (loan_purpose == 'car') * -1.0
        + (has_guarantor := rng.binomial(1, np.clip(0.18 + (requested_amount > 700000) * 0.22, 0.05, 0.72))) * -1.1
        + rng.normal(0, 1.6, n_rows),
        7.5,
        34.5,
    )

    collateral_type = np.where(
        loan_purpose == 'mortgage',
        'real_estate',
        np.where(
            loan_purpose == 'car',
            'car',
            np.where(has_guarantor == 1, 'guarantor', weighted_choice(rng, COLLATERAL_TYPES, [0.78, 0.06, 0.08, 0.08], n_rows)),
        ),
    )

    tenure_months = clip_round(
        np.select(
            [
                loan_purpose == 'consumer',
                loan_purpose == 'repair',
                loan_purpose == 'car',
                loan_purpose == 'education',
                loan_purpose == 'refinancing',
                loan_purpose == 'mortgage',
            ],
            [24, 30, 48, 36, 42, 180],
            default=30,
        )
        + rng.normal(0, 8, n_rows),
        6,
        240,
    )

    monthly_rate = loan_rate / 12 / 100
    payment_capacity_ratio = np.clip(
        0.52
        - risk_pressure * 0.22
        + has_guarantor * 0.04
        + owns_real_estate * 0.03
        + is_salary_client * 0.03
        + rng.normal(0, 0.025, n_rows),
        0.18,
        0.62,
    )
    affordable_payment = np.clip(monthly_income * payment_capacity_ratio, 3000, monthly_income * 0.62)

    annuity_factor = np.where(
        monthly_rate > 1e-9,
        monthly_rate / (1 - np.power(1 + monthly_rate, -np.maximum(tenure_months, 1))),
        1 / np.maximum(tenure_months, 1),
    )

    approval_headroom = np.clip(
        1.02
        - risk_pressure * 0.16
        + has_guarantor * 0.04
        + owns_real_estate * 0.03
        + is_salary_client * 0.02,
        0.72,
        1.08,
    )
    max_affordable_amount = affordable_payment / np.maximum(annuity_factor, 1e-9)
    approved_amount = np.minimum(requested_amount, max_affordable_amount * approval_headroom)
    approved_amount = np.clip(approved_amount, 50000, requested_amount)

    monthly_payment = approved_amount * annuity_factor
    monthly_payment = np.clip(monthly_payment, 3000, monthly_income * 0.62)

    dti_ratio = np.clip((monthly_payment + total_expenses * 0.35) / np.maximum(monthly_income, 1), 0.05, 1.35)
    payment_to_income_ratio = np.clip(monthly_payment / np.maximum(monthly_income, 1), 0.02, 0.95)

    delinquency_risk = np.clip(
        0.02
        + (dti_ratio > 0.55) * 0.13
        + (payment_to_income_ratio > 0.45) * 0.12
        + (income_source == 'business') * 0.05
        + (income_source == 'self_employed') * 0.03
        + (has_autopayment == 0) * 0.02
        - is_salary_client * 0.03
        - owns_real_estate * 0.02,
        0.01,
        0.75,
    )
    had_delinquency = rng.binomial(1, delinquency_risk, n_rows)
    num_past_delinquencies = np.where(had_delinquency == 1, clip_round(rng.poisson(1.8 + risk_pressure * 2.5, n_rows), 1, 9), 0)
    total_overdue_days = np.where(
        had_delinquency == 1,
        clip_round(rng.gamma(2.5, 10 + risk_pressure * 18, n_rows), 1, 360),
        0,
    )
    max_overdue_days = np.where(
        total_overdue_days > 0,
        np.minimum(total_overdue_days, clip_round(total_overdue_days * rng.uniform(0.18, 0.72, n_rows), 1, 180)),
        0,
    )
    has_bankruptcy = np.where(
        (total_overdue_days > 120) & (payment_to_income_ratio > 0.65),
        rng.binomial(1, 0.12, n_rows),
        rng.binomial(1, 0.01, n_rows),
    )

    premium_category = weighted_choice(rng, PREMIUM_CATEGORIES, [0.18, 0.16, 0.31, 0.35], n_rows)

    df = pd.DataFrame(
        {
            'marital_status': marital_status,
            'living_area_sqm': living_area_sqm.round(0).astype(int),
            'children_count': children_count,
            'monthly_income': monthly_income.round(0).astype(int),
            'income_source': income_source,
            'total_expenses': total_expenses.round(0).astype(int),
            'dti_ratio': np.round(dti_ratio, 3),
            'avg_monthly_turnover': avg_monthly_turnover.round(0).astype(int),
            'has_credit_card': has_credit_card,
            'num_credit_contracts': num_credit_contracts,
            'num_closed_loans': num_closed_loans,
            'total_overdue_days': total_overdue_days,
            'max_overdue_days': max_overdue_days,
            'num_past_delinquencies': num_past_delinquencies,
            'has_bankruptcy': has_bankruptcy,
            'avg_transaction_amount': avg_transaction_amount.round(0).astype(int),
            'num_transactions_monthly': num_transactions_monthly,
            'premium_category': premium_category,
            'uses_mobile_banking': uses_mobile_banking,
            'uses_investment_products': uses_investment_products,
            'has_autopayment': has_autopayment,
            'employment_type': employment_type,
            'employer_industry': employer_industry,
            'position_level': position_level,
            'work_experience_total_years': work_experience_total_years,
            'has_business': has_business,
            'business_profit': business_profit.round(0).astype(int),
            'owns_car': owns_car,
            'car_value': car_value.round(0).astype(int),
            'owns_real_estate': owns_real_estate,
            'real_estate_count': real_estate_count,
            'owns_land': owns_land,
            'loan_purpose': loan_purpose,
            'requested_amount': requested_amount.round(0).astype(int),
            'approved_amount': approved_amount.round(0).astype(int),
            'loan_rate': np.round(loan_rate, 1),
            'monthly_payment': monthly_payment.round(0).astype(int),
            'payment_to_income_ratio': np.round(payment_to_income_ratio, 3),
            'collateral_type': collateral_type,
            'has_guarantor': has_guarantor,
            'has_higher_education': has_higher_education,
            'is_salary_client': is_salary_client,
            'is_premium_client': is_premium_client,
            'client_segment': client_segment,
            'tenure_months': tenure_months,
        }
    )

    return df


def main() -> None:
    df = build_dataset()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f'Saved realistic synthetic dataset: {OUTPUT_PATH}')
    print(df.head(3).to_string(index=False))
    print('\nSummary:')
    print(df[['monthly_income', 'total_expenses', 'monthly_payment', 'total_overdue_days']].describe().round(2).to_string())


if __name__ == '__main__':
    main()
