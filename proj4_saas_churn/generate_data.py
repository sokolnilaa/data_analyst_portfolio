"""
Generates a realistic (synthetic) SaaS subscription dataset: one row per customer,
with signup date, plan, MRR, usage metrics, support tickets, and churn date (if churned).
Churn probability is driven by real usage/engagement signals, not pure randomness.
"""
import numpy as np
import pandas as pd
from datetime import timedelta

rng = np.random.default_rng(21)
N = 3000
START = pd.Timestamp("2022-01-01")
END = pd.Timestamp("2024-12-31")

plans = ["Basic", "Pro", "Enterprise"]
plan_weights = [0.55, 0.35, 0.10]
plan_mrr = {"Basic": 29, "Pro": 99, "Enterprise": 499}

channels = ["Organic", "Paid Ads", "Referral", "Sales-led", "Content/SEO"]
channel_weights = [0.30, 0.25, 0.15, 0.15, 0.15]

signup_offsets = rng.integers(0, (END - START).days - 30, N)
signup_dates = START + pd.to_timedelta(signup_offsets, unit="D")

plan = rng.choice(plans, N, p=plan_weights)
channel = rng.choice(channels, N, p=channel_weights)

# usage / engagement metrics - these will drive churn
avg_logins_per_month = np.clip(rng.gamma(2.2, 4, N), 0.2, None).round(1)
support_tickets = rng.poisson(1.2, N)
nps_score = np.clip(rng.normal(35, 25, N), -100, 100).round(0)  # typical SaaS NPS distribution

df = pd.DataFrame({
    "customer_id": [f"S{200000+i}" for i in range(N)],
    "signup_date": signup_dates,
    "plan": plan,
    "acquisition_channel": channel,
    "mrr": pd.Series(plan).map(plan_mrr) * rng.uniform(0.9, 1.1, N),
    "avg_logins_per_month": avg_logins_per_month,
    "support_tickets_opened": support_tickets,
    "nps_score": nps_score,
})
df["mrr"] = df["mrr"].round(2)

# ---------------- CHURN LOGIC ----------------
# Monthly churn hazard depends on engagement: low logins, low NPS, many support tickets -> higher hazard
base_hazard = 0.028  # ~2.8% base monthly churn (typical SMB SaaS)
hazard = (
    base_hazard
    + (df["avg_logins_per_month"] < 3).astype(int) * 0.035
    + (df["nps_score"] < 0).astype(int) * 0.03
    + (df["support_tickets_opened"] >= 3).astype(int) * 0.02
    - (df["plan"] == "Enterprise").astype(int) * 0.018  # enterprise stickier (contracts, onboarding)
    - (df["acquisition_channel"] == "Sales-led").astype(int) * 0.012
)
hazard = hazard.clip(0.005, 0.20)

months_active = ((END - df["signup_date"]).dt.days // 30).clip(lower=1)

churn_month = []
for h, m_active in zip(hazard, months_active):
    churned_at = None
    for m in range(1, m_active + 1):
        if rng.random() < h:
            churned_at = m
            break
    churn_month.append(churned_at)

df["months_to_churn"] = churn_month
df["churn_date"] = [
    (sd + pd.DateOffset(months=int(m))) if pd.notna(m) else pd.NaT
    for sd, m in zip(df["signup_date"], df["months_to_churn"])
]
# cap churn dates beyond our observation window as "still active" (right-censored)
df.loc[df["churn_date"] > END, "churn_date"] = pd.NaT
df["is_churned"] = df["churn_date"].notna()

df = df.drop(columns=["months_to_churn"])

# ---------------- inject realistic messiness ----------------
# missing NPS scores (not everyone responds to surveys - very realistic)
df.loc[df.sample(frac=0.25, random_state=1).index, "nps_score"] = np.nan
# a few duplicate rows
dupes = df.sample(n=12, random_state=2)
df = pd.concat([df, dupes], ignore_index=True)
df = df.sample(frac=1, random_state=3).reset_index(drop=True)

df.to_csv("data/saas_subscriptions.csv", index=False)
print(df.shape)
print("Churn rate (of observation-eligible):", df["is_churned"].mean())
