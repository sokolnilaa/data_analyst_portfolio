"""
Project 1: E-Commerce Sales & Customer Segmentation Analysis
Business question: Where is revenue coming from, which customers are most
valuable, and which are at risk of churning?
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 130

customers = pd.read_csv("data/customers.csv", parse_dates=["signup_date"])
orders = pd.read_csv("data/orders.csv", parse_dates=["order_date"])

log = []  # data-quality log for the report

# ---------------- CLEANING ----------------
n_before = len(orders)

# 1. Standardize country names
country_map = {"united kingdom": "United Kingdom", "UK": "United Kingdom", "USA": "United States"}
customers["country"] = customers["country"].replace(country_map)

# 2. Drop exact duplicate order rows
dupes = orders.duplicated().sum()
orders = orders.drop_duplicates()
log.append(f"Removed {dupes} exact duplicate order rows.")

# 3. Fix negative quantities (return rows mis-entered as orders) -> treat as returns, exclude from revenue
returns = orders[orders["quantity"] < 0].copy()
orders = orders[orders["quantity"] >= 0].copy()
log.append(f"Identified {len(returns)} rows with negative quantity (data-entry errors / returns) and excluded from revenue.")

# 4. Fix pricing outliers using IQR on unit_price per category
def cap_outliers(group):
    q1, q3 = group["unit_price"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper = q3 + 3 * iqr
    n_flagged = (group["unit_price"] > upper).sum()
    group.loc[group["unit_price"] > upper, "unit_price"] = np.nan
    return group, n_flagged

fixed_groups = []
total_flagged = 0
for cat, grp in orders.groupby("product_category"):
    fg, nf = cap_outliers(grp)
    fixed_groups.append(fg)
    total_flagged += nf
orders = pd.concat(fixed_groups)
log.append(f"Flagged {total_flagged} unit_price outliers (>3xIQR above Q3 per category) as missing, pending re-verification with finance.")

# 5. Impute missing discount_pct with 0 (no discount recorded = none applied), impute missing price with category median
orders["discount_pct"] = orders["discount_pct"].fillna(0)
orders["unit_price"] = orders.groupby("product_category")["unit_price"].transform(lambda x: x.fillna(x.median()))
log.append("Filled missing discount_pct with 0 and missing unit_price with category median.")

# 6. Impute missing customer age with overall median (flagged, not used for revenue calcs)
customers["age"] = customers["age"].fillna(customers["age"].median())

orders["revenue"] = orders["unit_price"] * orders["quantity"] * (1 - orders["discount_pct"])

n_after = len(orders)
log.append(f"Row count: {n_before} raw -> {n_after} clean (after removing duplicates/returns).")

with open("data_quality_log.txt", "w") as f:
    f.write("DATA QUALITY LOG\n" + "="*40 + "\n")
    for line in log:
        f.write("- " + line + "\n")

# ---------------- KPI: MONTHLY REVENUE TREND ----------------
orders["order_month"] = orders["order_date"].dt.to_period("M").dt.to_timestamp()
monthly_rev = orders.groupby("order_month")["revenue"].sum().reset_index()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(monthly_rev["order_month"], monthly_rev["revenue"], marker="o", color="#2E86AB", linewidth=2)
ax.set_title("Monthly Revenue Trend (2023-2024)", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (£)")
ax.set_xlabel("Month")
ax.fill_between(monthly_rev["order_month"], monthly_rev["revenue"], alpha=0.1, color="#2E86AB")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("charts/01_monthly_revenue_trend.png")
plt.close()

# ---------------- KPI: REVENUE BY CATEGORY ----------------
cat_rev = orders.groupby("product_category")["revenue"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=cat_rev.values, y=cat_rev.index, ax=ax, palette="viridis")
ax.set_title("Total Revenue by Product Category", fontsize=13, fontweight="bold")
ax.set_xlabel("Revenue (£)")
plt.tight_layout()
plt.savefig("charts/02_revenue_by_category.png")
plt.close()

# ---------------- RFM SEGMENTATION ----------------
snapshot_date = orders["order_date"].max() + pd.Timedelta(days=1)
rfm = orders.groupby("customer_id").agg(
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("revenue", "sum"),
).reset_index()

rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)
rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

def segment(row):
    if row["rfm_score"] >= 10:
        return "Champions"
    elif row["rfm_score"] >= 8:
        return "Loyal Customers"
    elif row["r_score"] <= 2 and row["f_score"] >= 3:
        return "At Risk"
    elif row["r_score"] <= 2 and row["f_score"] <= 2:
        return "Lost / Churned"
    else:
        return "Potential Loyalist"

rfm["segment"] = rfm.apply(segment, axis=1)
rfm.to_csv("data/rfm_segments.csv", index=False)

seg_summary = rfm.groupby("segment").agg(
    customers=("customer_id", "count"),
    avg_monetary=("monetary", "mean"),
    total_monetary=("monetary", "sum"),
).sort_values("total_monetary", ascending=False)
seg_summary.to_csv("data/segment_summary.csv")

fig, ax = plt.subplots(figsize=(9, 5))
seg_order = seg_summary.index
sns.barplot(x=seg_summary["customers"], y=seg_order, ax=ax, palette="magma")
ax.set_title("Customer Count by RFM Segment", fontsize=13, fontweight="bold")
ax.set_xlabel("Number of Customers")
plt.tight_layout()
plt.savefig("charts/03_rfm_segments.png")
plt.close()

# ---------------- COHORT RETENTION ----------------
orders_c = orders.merge(customers[["customer_id", "signup_date"]], on="customer_id")
orders_c["cohort_month"] = orders_c["signup_date"].dt.to_period("M")
orders_c["order_period"] = orders_c["order_date"].dt.to_period("M")
orders_c["period_number"] = (orders_c["order_period"] - orders_c["cohort_month"]).apply(lambda x: x.n)

cohort_data = orders_c.groupby(["cohort_month", "period_number"])["customer_id"].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index="cohort_month", columns="period_number", values="customer_id")
cohort_size = cohort_pivot.iloc[:, 0]
retention = cohort_pivot.divide(cohort_size, axis=0)
retention = retention.iloc[:12, :7]  # first 12 cohorts, first 7 months for readability

fig, ax = plt.subplots(figsize=(10, 7))
sns.heatmap(retention, annot=True, fmt=".0%", cmap="Blues", ax=ax, cbar_kws={"label": "Retention %"})
ax.set_title("Monthly Cohort Retention (% of cohort still ordering)", fontsize=13, fontweight="bold")
ax.set_xlabel("Months Since Signup")
ax.set_ylabel("Signup Cohort")
plt.tight_layout()
plt.savefig("charts/04_cohort_retention.png")
plt.close()

# ---------------- SUMMARY STATS FOR REPORT ----------------
total_revenue = orders["revenue"].sum()
total_orders = orders["order_id"].nunique()
aov = total_revenue / total_orders
top_category = cat_rev.idxmax()
champions_pct = (rfm["segment"] == "Champions").mean()
at_risk_customers = rfm[rfm["segment"] == "At Risk"]
at_risk_value = at_risk_customers["monetary"].sum()

summary = f"""
KEY METRICS
-----------
Total Revenue (cleaned):      £{total_revenue:,.0f}
Total Orders:                 {total_orders:,}
Average Order Value:          £{aov:,.2f}
Top Revenue Category:         {top_category}
% Customers who are Champions:{champions_pct:.1%}
'At Risk' segment size:       {len(at_risk_customers)} customers, £{at_risk_value:,.0f} in historical value
"""
with open("summary_stats.txt", "w") as f:
    f.write(summary)

print(summary)
print(seg_summary)
