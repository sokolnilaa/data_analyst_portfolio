"""
Project 2: Marketing Channel ROI & Checkout A/B Test Analysis
Business questions:
 1. Which marketing channels give the best return, and which should get more/less budget?
 2. Did the new checkout design actually improve conversion, or could the lift be due to chance?
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 130

# ================= PART 1: CHANNEL PERFORMANCE =================
perf = pd.read_csv("data/channel_performance.csv", parse_dates=["date"])

log = []
n_before = len(perf)
dupes = perf.duplicated().sum()
perf = perf.drop_duplicates()
log.append(f"Removed {dupes} duplicate rows (system double-export).")

missing_spend = perf["spend"].isna().sum()
perf["spend"] = perf.groupby("channel")["spend"].transform(lambda x: x.fillna(x.median()))
log.append(f"Imputed {missing_spend} missing spend values with channel median.")

perf["ctr"] = perf["clicks"] / perf["impressions"]
perf["cvr"] = perf["conversions"] / perf["clicks"]
perf["cac"] = perf["spend"] / perf["conversions"].replace(0, np.nan)
perf["roas"] = perf["revenue"] / perf["spend"]

channel_summary = perf.groupby("channel").agg(
    total_spend=("spend", "sum"),
    total_conversions=("conversions", "sum"),
    total_revenue=("revenue", "sum"),
).reset_index()
channel_summary["cac"] = channel_summary["total_spend"] / channel_summary["total_conversions"]
channel_summary["roas"] = channel_summary["total_revenue"] / channel_summary["total_spend"]
channel_summary = channel_summary.sort_values("roas", ascending=False)
channel_summary.to_csv("data/channel_summary.csv", index=False)

with open("data_quality_log.txt", "w") as f:
    f.write("DATA QUALITY LOG\n" + "="*40 + "\n")
    for line in log:
        f.write("- " + line + "\n")

# Chart: ROAS by channel
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#2E86AB" if r >= 1 else "#C94C4C" for r in channel_summary["roas"]]
ax.barh(channel_summary["channel"], channel_summary["roas"], color=colors)
ax.axvline(1, color="black", linestyle="--", linewidth=1, label="Break-even (ROAS = 1)")
ax.set_title("Return on Ad Spend (ROAS) by Channel", fontsize=13, fontweight="bold")
ax.set_xlabel("ROAS (Revenue / Spend)")
ax.legend()
plt.tight_layout()
plt.savefig("charts/01_roas_by_channel.png")
plt.close()

# Chart: CAC by channel
fig, ax = plt.subplots(figsize=(9, 5))
cac_sorted = channel_summary.sort_values("cac")
sns.barplot(data=cac_sorted, x="cac", y="channel", hue="channel", legend=False, palette="crest", ax=ax)
ax.set_title("Customer Acquisition Cost (CAC) by Channel", fontsize=13, fontweight="bold")
ax.set_xlabel("CAC (£ per conversion)")
plt.tight_layout()
plt.savefig("charts/02_cac_by_channel.png")
plt.close()

# Chart: Spend vs Revenue trend over time (top 3 channels)
top3 = channel_summary.head(3)["channel"].tolist()
trend = perf[perf["channel"].isin(top3)].groupby(["date", "channel"])["revenue"].sum().reset_index()
fig, ax = plt.subplots(figsize=(11, 5))
for ch in top3:
    sub = trend[trend["channel"] == ch]
    ax.plot(sub["date"], sub["revenue"], label=ch, linewidth=1.5)
ax.set_title("Daily Revenue Trend — Top 3 Channels by ROAS", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (£)")
ax.legend()
plt.tight_layout()
plt.savefig("charts/03_top_channel_trend.png")
plt.close()

# ================= PART 2: A/B TEST =================
ab = pd.read_csv("data/ab_test_checkout.csv")

summary_ab = ab.groupby("group").agg(
    users=("user_id", "count"),
    conversions=("converted", "sum"),
    conversion_rate=("converted", "mean"),
).reset_index()
summary_ab.to_csv("data/ab_test_summary.csv", index=False)

# Two-proportion z-test
control = ab[ab["group"] == "control"]
treatment = ab[ab["group"] == "treatment"]
n1, n2 = len(control), len(treatment)
x1, x2 = control["converted"].sum(), treatment["converted"].sum()
p1, p2 = x1 / n1, x2 / n2
p_pool = (x1 + x2) / (n1 + n2)
se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
z_stat = (p2 - p1) / se
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

# 95% CI on the lift
se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
ci_low = (p2 - p1) - 1.96 * se_diff
ci_high = (p2 - p1) + 1.96 * se_diff

relative_lift = (p2 - p1) / p1

ab_result = f"""
A/B TEST RESULT: Checkout Redesign
-----------------------------------
Control conversion rate:    {p1:.2%}  (n={n1:,}, conversions={x1:,})
Treatment conversion rate:  {p2:.2%}  (n={n2:,}, conversions={x2:,})
Absolute lift:              {(p2-p1):.2%}
Relative lift:              {relative_lift:.1%}
95% CI on absolute lift:    [{ci_low:.2%}, {ci_high:.2%}]
Z-statistic:                {z_stat:.3f}
P-value:                    {p_value:.4f}
Statistically significant at 95% confidence: {"YES" if p_value < 0.05 else "NO"}
"""
with open("ab_test_result.txt", "w") as f:
    f.write(ab_result)
print(ab_result)

# Chart: A/B conversion rate comparison with CI
fig, ax = plt.subplots(figsize=(7, 5))
rates = [p1, p2]
errors = [1.96 * np.sqrt(p1*(1-p1)/n1), 1.96 * np.sqrt(p2*(1-p2)/n2)]
bars = ax.bar(["Control", "Treatment"], rates, yerr=errors, capsize=8,
              color=["#8C8C8C", "#2E86AB"])
ax.set_title(f"Checkout A/B Test: Conversion Rate (p={p_value:.4f})", fontsize=13, fontweight="bold")
ax.set_ylabel("Conversion Rate")
for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width()/2, rate + 0.008, f"{rate:.1%}", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig("charts/04_ab_test_conversion.png")
plt.close()

# Chart: conversion rate by device, split by group (checking for interaction effects)
device_split = ab.groupby(["device", "group"])["converted"].mean().reset_index()
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(data=device_split, x="device", y="converted", hue="group", ax=ax, palette=["#8C8C8C", "#2E86AB"])
ax.set_title("Conversion Rate by Device & Test Group", fontsize=13, fontweight="bold")
ax.set_ylabel("Conversion Rate")
plt.tight_layout()
plt.savefig("charts/05_ab_test_by_device.png")
plt.close()

print(channel_summary)
