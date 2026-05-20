# file: generate_finance_demo_dataset.py
"""
Generate a realistic synthetic finance demo dataset with 3 Excel sheets:
- transactions (5000 rows)
- budgets
- portfolio

Outputs:
- finance_demo_dataset.xlsx
- finance_demo_transactions.csv
- finance_demo_budgets.csv
- finance_demo_portfolio.csv
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd


SEED = 42
N_TRANSACTIONS = 5000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 5, 20)


@dataclass(frozen=True)
class CategoryProfile:
    amount_range: Tuple[float, float]
    merchants: Tuple[str, ...]
    monthly_budget_range: Tuple[float, float]


CATEGORY_PROFILES: Dict[str, CategoryProfile] = {
    "Groceries": CategoryProfile((12, 280), ("Walmart", "Costco", "Whole Foods", "Trader Joe's"), (600, 1100)),
    "Housing": CategoryProfile((900, 2600), ("Monthly Rent", "Property Mgmt", "Housing Society"), (1800, 2800)),
    "Utilities": CategoryProfile((35, 320), ("Electricity Board", "Water Utility", "Comcast", "Gas Provider"), (250, 500)),
    "Transport": CategoryProfile((8, 180), ("Uber", "Lyft", "Shell", "Metro Transit"), (250, 700)),
    "Dining": CategoryProfile((10, 170), ("Starbucks", "Chipotle", "McDonald's", "Olive Garden"), (300, 750)),
    "Shopping": CategoryProfile((20, 800), ("Amazon", "Target", "Best Buy", "Macy's"), (350, 900)),
    "Healthcare": CategoryProfile((25, 1400), ("CVS Pharmacy", "City Clinic", "LabCorp", "Health Insurance"), (250, 900)),
    "Entertainment": CategoryProfile((8, 260), ("Netflix", "Spotify", "AMC Theatres", "Steam"), (120, 450)),
    "Education": CategoryProfile((30, 1800), ("Coursera", "Udemy", "Bookstore", "Exam Board"), (120, 600)),
    "Travel": CategoryProfile((80, 3500), ("Delta Airlines", "Marriott", "Airbnb", "Booking.com"), (200, 1200)),
}


PORTFOLIO_UNIVERSE = [
    ("AAPL", "Apple Inc.", 170, 235),
    ("MSFT", "Microsoft Corp.", 280, 460),
    ("GOOGL", "Alphabet Inc.", 95, 210),
    ("AMZN", "Amazon.com Inc.", 90, 220),
    ("NVDA", "NVIDIA Corp.", 180, 1200),
    ("META", "Meta Platforms Inc.", 140, 600),
    ("JPM", "JPMorgan Chase", 110, 260),
    ("V", "Visa Inc.", 180, 340),
    ("JNJ", "Johnson & Johnson", 140, 210),
    ("XOM", "Exxon Mobil Corp.", 80, 140),
    ("TSLA", "Tesla Inc.", 120, 420),
    ("VOO", "Vanguard S&P 500 ETF", 330, 560),
]


def random_date(start: datetime, end: datetime) -> datetime:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_transactions(n: int = N_TRANSACTIONS) -> pd.DataFrame:
    rows: List[dict] = []
    categories = list(CATEGORY_PROFILES.keys())

    for _ in range(n):
        category = random.choice(categories)
        profile = CATEGORY_PROFILES[category]
        merchant = random.choice(profile.merchants)

        base_low, base_high = profile.amount_range
        amount = random.uniform(base_low, base_high)

        # Inject occasional high-value anomalies (~1.8%)
        if random.random() < 0.018:
            amount *= random.uniform(2.5, 6.0)

        txn_date = random_date(START_DATE, END_DATE)

        rows.append(
            {
                "date": txn_date.strftime("%Y-%m-%d"),
                "description": merchant,
                "amount": round(amount, 2),
                "category": category,
            }
        )

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def generate_budgets() -> pd.DataFrame:
    rows: List[dict] = []
    for category, profile in CATEGORY_PROFILES.items():
        budget = random.uniform(*profile.monthly_budget_range)
        rows.append(
            {
                "category": category,
                "budget_amount": round(budget, 2),
            }
        )
    return pd.DataFrame(rows).sort_values("category").reset_index(drop=True)


def generate_portfolio() -> pd.DataFrame:
    picks = random.sample(PORTFOLIO_UNIVERSE, k=8)
    rows: List[dict] = []

    for symbol, security_name, min_price, max_price in picks:
        avg_price = round(random.uniform(min_price * 0.8, max_price * 0.9), 2)
        current_price = round(random.uniform(min_price, max_price), 2)
        quantity = round(random.uniform(8, 220), 2)

        rows.append(
            {
                "symbol": symbol,
                "security_name": security_name,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,  # extra field (optional for your app)
            }
        )

    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def main() -> None:
    random.seed(SEED)

    transactions_df = generate_transactions(N_TRANSACTIONS)
    budgets_df = generate_budgets()
    portfolio_df = generate_portfolio()

    excel_path = "finance_demo_dataset.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        transactions_df.to_excel(writer, sheet_name="transactions", index=False)
        budgets_df.to_excel(writer, sheet_name="budgets", index=False)
        portfolio_df.to_excel(writer, sheet_name="portfolio", index=False)

    transactions_df.to_csv("finance_demo_transactions.csv", index=False)
    budgets_df.to_csv("finance_demo_budgets.csv", index=False)
    portfolio_df.to_csv("finance_demo_portfolio.csv", index=False)

    print("Generated files:")
    print(f"- {excel_path} (3 sheets: transactions, budgets, portfolio)")
    print("- finance_demo_transactions.csv")
    print("- finance_demo_budgets.csv")
    print("- finance_demo_portfolio.csv")
    print("\nSample counts:")
    print(f"transactions: {len(transactions_df)}")
    print(f"budgets: {len(budgets_df)}")
    print(f"portfolio: {len(portfolio_df)}")


if __name__ == "__main__":
    main()