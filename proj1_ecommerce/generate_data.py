"""
Generates a realistic (synthetic) e-commerce transactional dataset:
customers.csv and orders.csv

Realism baked in on purpose (so the cleaning step has real work to do):
- Seasonal sales spike (Nov/Dec)
- Missing values in a few columns
- Duplicate order rows
- A handful of pricing outliers / data entry errors
- Inconsistent country name casing
- Some customers who churn (no orders in the last 6 months)
"""
import numpy as np
import pandas as pd
from datetime import timedelta

rng = np.random.default_rng(42)

N_CUSTOMERS = 2500
START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2024-12-31")

countries = ["United Kingdom", "united kingdom", "UK", "United States", "USA",
             "Germany", "France", "Spain", "Ireland"]
country_weights = [0.28, 0.05, 0.05, 0.20, 0.05, 0.15, 0.12, 0.06, 0.04]

channels = ["Organic Search", "Paid Social", "Email", "Referral", "Direct", "Paid Search"]
channel_weights = [0.25, 0.20, 0.15, 0.10, 0.15, 0.15]

categories = {
    "Electronics": (40, 900),
    "Home & Kitchen": (10, 250),
    "Apparel": (8, 150),
    "Beauty": (5, 90),
    "Sports & Outdoors": (12, 300),
    "Books": (5, 45),
    "Toys": (6, 120),
}

# ---------- customers ----------
signup_dates = START_DATE + pd.to_timedelta(
    rng.integers(0, (END_DATE - START_DATE).days - 30, N_CUSTOMERS), unit="D"
)
customers = pd.DataFrame({
    "customer_id": [f"C{100000+i}" for i in range(N_CUSTOMERS)],
    "signup_date": signup_dates,
    "country": rng.choice(countries, N_CUSTOMERS, p=country_weights),
    "age": rng.integers(18, 75, N_CUSTOMERS),
    "acquisition_channel": rng.choice(channels, N_CUSTOMERS, p=channel_weights),
})
# sprinkle some missing ages (real CRM data is never complete)
customers.loc[rng.choice(N_CUSTOMERS, 120, replace=False), "age"] = np.nan

# ---------- orders ----------
# Give each customer a "purchase propensity" so some are frequent buyers, most aren't (realistic long tail)
propensity = rng.gamma(shape=1.5, scale=1.2, size=N_CUSTOMERS)
propensity = propensity / propensity.mean()

rows = []
order_counter = 500000
for idx, cust in customers.iterrows():
    active_days = (END_DATE - cust["signup_date"]).days
    if active_days <= 0:
        continue
    # ~15% of customers churn early and stop ordering after their first few purchases
    is_churner = rng.random() < 0.15
    expected_orders = max(1, int(rng.poisson(3 * propensity[idx])))
    if is_churner:
        expected_orders = min(expected_orders, 3)

    for _ in range(expected_orders):
        if is_churner:
            # all orders bunched in first 4 months after signup
            day_offset = rng.integers(0, min(120, active_days) or 1)
        else:
            day_offset = rng.integers(0, active_days)
        order_date = cust["signup_date"] + timedelta(days=int(day_offset))

        # seasonal boost: Nov/Dec orders get duplicated more often (holiday rush -> more data entry issues too)
        seasonal_multiplier = 1.6 if order_date.month in (11, 12) else 1.0
        if rng.random() > (0.55 / seasonal_multiplier):
            continue  # skip to keep monthly volume realistic while still peaking in Nov/Dec

        category = rng.choice(list(categories.keys()))
        lo, hi = categories[category]
        unit_price = round(rng.uniform(lo, hi), 2)
        quantity = rng.choice([1, 1, 1, 2, 2, 3], p=[0.45, 0.2, 0.15, 0.1, 0.05, 0.05])
        discount = rng.choice([0, 0, 0, 0.1, 0.15, 0.2], p=[0.55, 0.15, 0.1, 0.1, 0.05, 0.05])

        rows.append({
            "order_id": f"ORD{order_counter}",
            "customer_id": cust["customer_id"],
            "order_date": order_date,
            "product_category": category,
            "unit_price": unit_price,
            "quantity": quantity,
            "discount_pct": discount,
        })
        order_counter += 1

orders = pd.DataFrame(rows)

# --- inject realistic messiness ---
# 1. duplicate ~1.5% of rows (system double-submits)
dupes = orders.sample(frac=0.015, random_state=1)
orders = pd.concat([orders, dupes], ignore_index=True)

# 2. missing discount_pct on ~3% of rows
orders.loc[orders.sample(frac=0.03, random_state=2).index, "discount_pct"] = np.nan

# 3. a few pricing outliers / entry errors (e.g. missing decimal point)
outlier_idx = orders.sample(n=15, random_state=3).index
orders.loc[outlier_idx, "unit_price"] = orders.loc[outlier_idx, "unit_price"] * 100

# 4. a few negative quantities (return/refund rows entered incorrectly as orders)
neg_idx = orders.sample(n=10, random_state=4).index
orders.loc[neg_idx, "quantity"] = -orders.loc[neg_idx, "quantity"]

# 5. shuffle row order (real exports aren't sorted)
orders = orders.sample(frac=1, random_state=5).reset_index(drop=True)

customers.to_csv("data/customers.csv", index=False)
orders.to_csv("data/orders.csv", index=False)

print(f"customers: {customers.shape}, orders: {orders.shape}")
print(orders.head())
