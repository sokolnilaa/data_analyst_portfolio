"""
Project 3: HR Employee Attrition Analysis
Business question: Why are we losing employees, and which factors actually predict attrition
vs. which are just noise? What should HR act on first?
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 130

df = pd.read_csv("data/hr_employees.csv")

log = []
n_before = len(df)

# ---------------- CLEANING ----------------
dupes = df.duplicated(subset=[c for c in df.columns if c != "employee_id"]).sum()
df = df.drop_duplicates(subset=[c for c in df.columns if c != "employee_id"])
log.append(f"Removed {dupes} duplicate employee records (same profile, likely system merge duplicates).")

miss_sat = df["job_satisfaction"].isna().sum()
df["job_satisfaction"] = df["job_satisfaction"].fillna(df["job_satisfaction"].median())
log.append(f"Imputed {miss_sat} missing job_satisfaction values with the median.")

miss_dist = df["distance_from_home_km"].isna().sum()
df["distance_from_home_km"] = df["distance_from_home_km"].fillna(df["distance_from_home_km"].median())
log.append(f"Imputed {miss_dist} missing distance_from_home_km values with the median.")

log.append(f"Row count: {n_before} raw -> {len(df)} clean.")
with open("data_quality_log.txt", "w") as f:
    f.write("DATA QUALITY LOG\n" + "="*40 + "\n")
    for line in log:
        f.write("- " + line + "\n")

overall_attrition = (df["attrition"] == "Yes").mean()

# ---------------- CHI-SQUARE TESTS (categorical drivers) ----------------
cat_vars = ["overtime", "department", "job_level"]
chi_results = []
for var in cat_vars:
    ct = pd.crosstab(df[var], df["attrition"])
    chi2, p, dof, exp = stats.chi2_contingency(ct)
    chi_results.append({"variable": var, "chi2": round(chi2, 2), "p_value": round(p, 5),
                         "significant_0.05": p < 0.05})
chi_df = pd.DataFrame(chi_results)
chi_df.to_csv("data/chi_square_results.csv", index=False)

# ---------------- T-TESTS (continuous drivers) ----------------
cont_vars = ["job_satisfaction", "work_life_balance", "monthly_income",
             "years_since_last_promotion", "distance_from_home_km", "years_at_company"]
t_results = []
for var in cont_vars:
    left = df.loc[df["attrition"] == "Yes", var]
    stayed = df.loc[df["attrition"] == "No", var]
    t_stat, p = stats.ttest_ind(left, stayed, equal_var=False)
    t_results.append({
        "variable": var,
        "mean_attrition_yes": round(left.mean(), 2),
        "mean_attrition_no": round(stayed.mean(), 2),
        "t_stat": round(t_stat, 2),
        "p_value": round(p, 5),
        "significant_0.05": p < 0.05,
    })
t_df = pd.DataFrame(t_results).sort_values("p_value")
t_df.to_csv("data/t_test_results.csv", index=False)

# ---------------- LOGISTIC REGRESSION (relative driver strength) ----------------
model_df = df.copy()
model_df["attrition_flag"] = (model_df["attrition"] == "Yes").astype(int)
model_df["overtime_flag"] = (model_df["overtime"] == "Yes").astype(int)

features = ["job_satisfaction", "work_life_balance", "environment_satisfaction",
            "overtime_flag", "years_since_last_promotion", "distance_from_home_km",
            "monthly_income", "years_at_company", "job_level", "training_times_last_year"]

X = model_df[features]
y = model_df["attrition_flag"]
X_scaled = StandardScaler().fit_transform(X)

logit = LogisticRegression(max_iter=1000)
logit.fit(X_scaled, y)

coef_df = pd.DataFrame({
    "feature": features,
    "coefficient": logit.coef_[0],
}).sort_values("coefficient", key=abs, ascending=False)
coef_df["direction"] = coef_df["coefficient"].apply(lambda x: "increases attrition risk" if x > 0 else "decreases attrition risk")
coef_df.to_csv("data/logistic_regression_drivers.csv", index=False)

# ---------------- CHARTS ----------------
# 1. Attrition rate by overtime
fig, ax = plt.subplots(figsize=(7, 5))
rates = df.groupby("overtime")["attrition"].apply(lambda x: (x == "Yes").mean())
ax.bar(rates.index, rates.values, color=["#2E86AB", "#C94C4C"])
ax.axhline(overall_attrition, linestyle="--", color="grey", label=f"Company avg ({overall_attrition:.1%})")
ax.set_title("Attrition Rate: Overtime vs. No Overtime", fontsize=13, fontweight="bold")
ax.set_ylabel("Attrition Rate")
for i, v in enumerate(rates.values):
    ax.text(i, v + 0.01, f"{v:.1%}", ha="center", fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig("charts/01_attrition_by_overtime.png")
plt.close()

# 2. Attrition rate by job satisfaction level
fig, ax = plt.subplots(figsize=(8, 5))
rates2 = df.groupby("job_satisfaction")["attrition"].apply(lambda x: (x == "Yes").mean())
ax.bar(rates2.index.astype(str), rates2.values, color="#4C7A8C")
ax.set_title("Attrition Rate by Job Satisfaction (1=Low, 4=High)", fontsize=13, fontweight="bold")
ax.set_ylabel("Attrition Rate")
ax.set_xlabel("Job Satisfaction Score")
plt.tight_layout()
plt.savefig("charts/02_attrition_by_satisfaction.png")
plt.close()

# 3. Attrition rate by department
fig, ax = plt.subplots(figsize=(9, 5))
rates3 = df.groupby("department")["attrition"].apply(lambda x: (x == "Yes").mean()).sort_values(ascending=False)
sns.barplot(x=rates3.values, y=rates3.index, hue=rates3.index, legend=False, palette="rocket", ax=ax)
ax.axvline(overall_attrition, linestyle="--", color="grey")
ax.set_title("Attrition Rate by Department", fontsize=13, fontweight="bold")
ax.set_xlabel("Attrition Rate")
plt.tight_layout()
plt.savefig("charts/03_attrition_by_department.png")
plt.close()

# 4. Logistic regression driver strength (tornado chart)
fig, ax = plt.subplots(figsize=(9, 6))
colors = ["#C94C4C" if c > 0 else "#2E86AB" for c in coef_df["coefficient"]]
ax.barh(coef_df["feature"], coef_df["coefficient"], color=colors)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_title("What Predicts Attrition? (Logistic Regression Coefficients)", fontsize=13, fontweight="bold")
ax.set_xlabel("Coefficient (standardized) — right = increases risk, left = decreases risk")
plt.tight_layout()
plt.savefig("charts/04_attrition_drivers.png")
plt.close()

# 5. Correlation heatmap of numeric features
numeric_cols = ["age", "monthly_income", "years_at_company", "years_since_last_promotion",
                 "distance_from_home_km", "job_satisfaction", "work_life_balance",
                 "environment_satisfaction", "training_times_last_year"]
corr = df[numeric_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
ax.set_title("Correlation Matrix — Numeric HR Variables", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/05_correlation_heatmap.png")
plt.close()

summary = f"""
KEY METRICS
-----------
Overall attrition rate: {overall_attrition:.1%}
Employees analyzed:     {len(df):,}

Top statistically significant categorical drivers (chi-square, p<0.05):
{chi_df[chi_df['significant_0.05']].to_string(index=False)}

Top statistically significant continuous drivers (t-test, p<0.05):
{t_df[t_df['significant_0.05']].to_string(index=False)}

Top 3 logistic regression drivers by |coefficient|:
{coef_df.head(3).to_string(index=False)}
"""
with open("summary_stats.txt", "w") as f:
    f.write(summary)
print(summary)
