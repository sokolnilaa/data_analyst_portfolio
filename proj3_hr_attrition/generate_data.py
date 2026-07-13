"""
Generates a realistic (synthetic) HR employee dataset where attrition is driven by
a mix of real factors (low satisfaction, overtime, long commute, low pay relative to
role/level, few years since last promotion) plus some noise - just like a real HR dataset.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(11)
N = 1500

departments = ["Sales", "R&D", "HR", "Marketing", "Operations", "Finance"]
dept_weights = [0.28, 0.25, 0.07, 0.12, 0.18, 0.10]

job_levels = [1, 2, 3, 4, 5]
job_level_weights = [0.35, 0.30, 0.20, 0.10, 0.05]

df = pd.DataFrame({
    "employee_id": [f"E{10000+i}" for i in range(N)],
    "age": rng.integers(21, 60, N),
    "department": rng.choice(departments, N, p=dept_weights),
    "job_level": rng.choice(job_levels, N, p=job_level_weights),
    "monthly_income": None,
    "years_at_company": rng.integers(0, 20, N),
    "years_since_last_promotion": None,
    "distance_from_home_km": np.round(rng.exponential(8, N) + 1, 1),
    "overtime": rng.choice(["Yes", "No"], N, p=[0.30, 0.70]),
    "job_satisfaction": rng.integers(1, 5, N),  # 1=low, 4=high
    "work_life_balance": rng.integers(1, 5, N),
    "environment_satisfaction": rng.integers(1, 5, N),
    "performance_rating": rng.choice([3, 4], N, p=[0.85, 0.15]),  # most orgs rate most people "meets expectations"
    "training_times_last_year": rng.integers(0, 6, N),
})

# income depends on job level + some randomness (more realistic than pure random)
base_income_by_level = {1: 2800, 2: 4200, 3: 6000, 4: 8500, 5: 12000}
df["monthly_income"] = df["job_level"].map(base_income_by_level) * rng.uniform(0.85, 1.2, N)
df["monthly_income"] = df["monthly_income"].round(0)

# years since last promotion can't exceed years at company
df["years_since_last_promotion"] = [rng.integers(0, y + 1) if y > 0 else 0 for y in df["years_at_company"]]

# ---------------- ATTRITION LOGIC (the ground truth signal) ----------------
# Build a "risk score" from real drivers, then convert to probability
risk = (
    (df["job_satisfaction"] <= 2).astype(int) * 1.3
    + (df["work_life_balance"] <= 2).astype(int) * 1.0
    + (df["overtime"] == "Yes").astype(int) * 1.1
    + (df["years_since_last_promotion"] >= 5).astype(int) * 0.9
    + (df["distance_from_home_km"] >= 20).astype(int) * 0.6
    + (df["monthly_income"] < df["monthly_income"].median() * 0.7).astype(int) * 0.8
    + (df["years_at_company"] <= 1).astype(int) * 0.7  # new hires leave more (flight risk)
    - (df["job_level"] >= 4).astype(int) * 0.5  # senior staff more likely to stay
)
risk_scaled = (risk - risk.min()) / (risk.max() - risk.min())
prob_attrition = 0.05 + risk_scaled * 0.55  # baseline 5% up to ~60% for highest risk
df["attrition"] = rng.binomial(1, prob_attrition)
df["attrition"] = df["attrition"].map({1: "Yes", 0: "No"})

# ---------------- inject realistic messiness ----------------
# missing values in a couple of columns (HR systems always have gaps)
df.loc[df.sample(frac=0.02, random_state=1).index, "job_satisfaction"] = np.nan
df.loc[df.sample(frac=0.015, random_state=2).index, "distance_from_home_km"] = np.nan
# a few duplicate employee records (system merge issue)
dupes = df.sample(n=8, random_state=3)
df = pd.concat([df, dupes], ignore_index=True)
df = df.sample(frac=1, random_state=4).reset_index(drop=True)

df.to_csv("data/hr_employees.csv", index=False)
print(df.shape)
print(df["attrition"].value_counts(normalize=True))
