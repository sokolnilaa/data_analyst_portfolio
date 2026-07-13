"""
Project 4: SaaS Subscription Churn & Retention Analysis
Business question: What's our monthly churn rate, which customers/segments churn fastest,
and what's each plan actually worth to us over its lifetime (LTV)?
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 130

df = pd.read_csv("data/saas_subscriptions.csv", parse_dates=["signup_date", "churn_date"])

log = []
n_before = len(df)

# ---------------- CLEANING ----------------
dupes = df.duplicated(subset=[c for c in df.columns if c != "customer_id"]).sum()
df = df.drop_duplicates(subset=[c for c in df.columns if c != "customer_id"])
log.append(f"Removed {dupes} duplicate subscription records.")

missing_nps = df["nps_score"].isna().sum()
log.append(f"{missing_nps} rows ({missing_nps/len(df):.1%}) have no NPS score recorded (survey non-response) — "
            f"left as missing rather than imputed, since imputing sentiment data risks masking real signal.")

log.append(f"Row count: {n_before} raw -> {len(df)} clean.")
with open("data_quality_log.txt", "w") as f:
    f.write("DATA QUALITY LOG\n" + "="*40 + "\n")
    for line in log:
        f.write("- " + line + "\n")

OBS_END = pd.Timestamp("2024-12-31")

# ---------------- MONTHLY MRR & CHURN RATE TREND ----------------
months = pd.period_range(df["signup_date"].min(), OBS_END, freq="M")
mrr_trend = []
for m in months:
    month_end = m.to_timestamp("M")
    active_mask = (df["signup_date"] <= month_end) & ((df["churn_date"].isna()) | (df["churn_date"] > month_end))
    active = df[active_mask]

    prev_month_end = (m - 1).to_timestamp("M") if m != months[0] else None
    if prev_month_end is not None:
        active_start_mask = (df["signup_date"] <= prev_month_end) & ((df["churn_date"].isna()) | (df["churn_date"] > prev_month_end))
        n_start = active_start_mask.sum()
        churned_this_month = ((df["churn_date"].dt.to_period("M") == m)).sum()
        logo_churn_rate = churned_this_month / n_start if n_start > 0 else np.nan
    else:
        logo_churn_rate = np.nan

    mrr_trend.append({
        "month": month_end,
        "active_customers": len(active),
        "mrr": active["mrr"].sum(),
        "logo_churn_rate": logo_churn_rate,
    })

mrr_df = pd.DataFrame(mrr_trend)
mrr_df.to_csv("data/mrr_trend.csv", index=False)

fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.plot(mrr_df["month"], mrr_df["mrr"], color="#2E86AB", linewidth=2, label="MRR")
ax1.set_ylabel("MRR (£)", color="#2E86AB")
ax1.set_title("Monthly Recurring Revenue & Logo Churn Rate", fontsize=13, fontweight="bold")
ax2 = ax1.twinx()
ax2.plot(mrr_df["month"], mrr_df["logo_churn_rate"] * 100, color="#C94C4C", linewidth=1.5, linestyle="--", label="Logo churn %")
ax2.set_ylabel("Monthly Logo Churn Rate (%)", color="#C94C4C")
plt.tight_layout()
plt.savefig("charts/01_mrr_and_churn_trend.png")
plt.close()

# ---------------- COHORT RETENTION (logo-based) ----------------
df["cohort_month"] = df["signup_date"].dt.to_period("M")
max_period = pd.Period(OBS_END, freq="M")

cohort_rows = []
for cohort, grp in df.groupby("cohort_month"):
    cohort_size = len(grp)
    for offset in range(0, 13):
        check_period = cohort + offset
        if check_period > max_period:
            break
        check_date = check_period.to_timestamp("M")
        still_active = ((grp["churn_date"].isna()) | (grp["churn_date"] > check_date)).sum()
        cohort_rows.append({"cohort_month": cohort, "month_offset": offset, "retained_pct": still_active / cohort_size})

cohort_df = pd.DataFrame(cohort_rows)
cohort_pivot = cohort_df.pivot(index="cohort_month", columns="month_offset", values="retained_pct")
cohort_pivot = cohort_pivot.iloc[:12, :7]  # first 12 cohorts, 7 months for readability

fig, ax = plt.subplots(figsize=(10, 7))
sns.heatmap(cohort_pivot, annot=True, fmt=".0%", cmap="Blues", ax=ax, cbar_kws={"label": "% Retained"})
ax.set_title("Cohort Retention — % of Customers Still Subscribed", fontsize=13, fontweight="bold")
ax.set_xlabel("Months Since Signup")
ax.set_ylabel("Signup Cohort")
plt.tight_layout()
plt.savefig("charts/02_cohort_retention.png")
plt.close()

# ---------------- CHURN DRIVERS ----------------
chi_results = []
for var in ["plan", "acquisition_channel"]:
    ct = pd.crosstab(df[var], df["is_churned"])
    chi2, p, dof, exp = stats.chi2_contingency(ct)
    chi_results.append({"variable": var, "chi2": round(chi2, 2), "p_value": round(p, 5), "significant_0.05": p < 0.05})
chi_df = pd.DataFrame(chi_results)
chi_df.to_csv("data/chi_square_results.csv", index=False)

t_results = []
for var in ["avg_logins_per_month", "support_tickets_opened", "nps_score"]:
    sub = df.dropna(subset=[var])
    churned = sub.loc[sub["is_churned"], var]
    active = sub.loc[~sub["is_churned"], var]
    t_stat, p = stats.ttest_ind(churned, active, equal_var=False)
    t_results.append({
        "variable": var, "mean_churned": round(churned.mean(), 2), "mean_active": round(active.mean(), 2),
        "t_stat": round(t_stat, 2), "p_value": round(p, 5), "significant_0.05": p < 0.05,
    })
t_df = pd.DataFrame(t_results)
t_df.to_csv("data/t_test_results.csv", index=False)

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
for ax, var in zip(axes, ["avg_logins_per_month", "support_tickets_opened", "nps_score"]):
    sns.boxplot(data=df.dropna(subset=[var]), x="is_churned", y=var, hue="is_churned", legend=False,
                palette=["#2E86AB", "#C94C4C"], ax=ax)
    ax.set_xticklabels(["Active", "Churned"])
    ax.set_title(var.replace("_", " ").title(), fontsize=11, fontweight="bold")
    ax.set_xlabel("")
plt.suptitle("Engagement Metrics: Active vs. Churned Customers", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/03_churn_drivers_boxplots.png")
plt.close()

# ---------------- LTV BY PLAN ----------------
plan_churn = df.groupby("plan")["is_churned"].mean()
# crude monthly churn rate approximation: total churned / total customer-months observed, per plan
def monthly_churn_rate(grp):
    total_months = 0
    for _, row in grp.iterrows():
        end = row["churn_date"] if pd.notna(row["churn_date"]) else OBS_END
        months = max(1, (end.year - row["signup_date"].year) * 12 + (end.month - row["signup_date"].month))
        total_months += months
    return grp["is_churned"].sum() / total_months if total_months > 0 else np.nan

ltv_rows = []
for plan, grp in df.groupby("plan"):
    m_churn = monthly_churn_rate(grp)
    avg_mrr = grp["mrr"].mean()
    ltv = avg_mrr / m_churn if m_churn > 0 else np.nan
    ltv_rows.append({"plan": plan, "avg_mrr": round(avg_mrr, 2), "monthly_churn_rate": round(m_churn, 4),
                      "avg_lifetime_months": round(1 / m_churn, 1), "estimated_ltv": round(ltv, 2)})
ltv_df = pd.DataFrame(ltv_rows).sort_values("estimated_ltv", ascending=False)
ltv_df.to_csv("data/ltv_by_plan.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=ltv_df, x="plan", y="estimated_ltv", hue="plan", legend=False, palette="crest", ax=ax)
ax.set_title("Estimated Customer Lifetime Value (LTV) by Plan", fontsize=13, fontweight="bold")
ax.set_ylabel("Estimated LTV (£)")
for i, row in enumerate(ltv_df.itertuples()):
    ax.text(i, row.estimated_ltv + 20, f"£{row.estimated_ltv:,.0f}", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig("charts/04_ltv_by_plan.png")
plt.close()

# ---------------- SUMMARY ----------------
current_mrr = mrr_df["mrr"].iloc[-1]
avg_logo_churn = mrr_df["logo_churn_rate"].mean()
overall_churn_rate = df["is_churned"].mean()

summary = f"""
KEY METRICS
-----------
Current MRR (latest month): £{current_mrr:,.0f}
Average monthly logo churn rate: {avg_logo_churn:.2%}
Overall cumulative churn rate (of all customers ever signed up): {overall_churn_rate:.1%}

Chi-square (categorical drivers):
{chi_df.to_string(index=False)}

T-tests (engagement drivers, churned vs active):
{t_df.to_string(index=False)}

LTV by plan:
{ltv_df.to_string(index=False)}
"""
with open("summary_stats.txt", "w") as f:
    f.write(summary)
print(summary)
