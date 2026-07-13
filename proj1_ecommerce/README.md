# Project 1: E-Commerce Sales & Customer Segmentation Analysis

## Business question
"Where is our revenue coming from, which customers are most valuable, and which are at risk of leaving?"
This is the single most common brief a retail/e-commerce data analyst gets in their first month on the job.

## Data
`customers.csv` (2,500 rows) and `orders.csv` (~3,700 rows) — synthetic but built to mirror a real transactional
export: seasonal spikes, duplicate rows, missing values, pricing outliers, and negative-quantity data-entry errors.
*(Note for the interviewer: this dataset is generated to be realistically messy since I didn't have a live
production export to use — the cleaning and analysis techniques are identical to what I'd apply to a real one.)*

## What I did
1. **Cleaned the data** — removed exact duplicates, separated out negative-quantity rows (returns mis-entered
   as orders), flagged pricing outliers per-category using an IQR rule, and imputed missing values sensibly
   (median for prices, 0 for missing discounts). Every step is logged in `data_quality_log.txt` so the cleaning
   is auditable, not a black box.
2. **Built core KPIs** — monthly revenue trend, revenue by product category, average order value.
3. **RFM segmentation** — scored every customer on Recency, Frequency, and Monetary value, then bucketed them
   into segments (Champions, Loyal, At Risk, Lost, Potential Loyalist).
4. **Cohort retention analysis** — grouped customers by signup month and tracked what % of each cohort keeps
   ordering in the months after signup.

## Key findings
- Total cleaned revenue: **£597,520** across 3,602 orders (AOV: £165.89)
- **Electronics** is the top revenue category — worth checking if margin follows revenue or if it's a low-margin traffic driver
- 25% of customers are "Champions" and account for the majority of total revenue — classic Pareto pattern
- **132 customers (£19.5k historical value) are flagged "At Risk"** — they used to order frequently but haven't
  recently. This is the actionable list: a win-back campaign targeted at this exact group.
- Retention drops off sharply after month 1 for most cohorts — a strong signal that onboarding/second-purchase
  incentives would have more ROI than acquisition spend.

## Files
- `generate_data.py` — synthetic data generator
- `analysis.py` — cleaning, KPI calculation, RFM segmentation, cohort analysis
- `data/` — raw and cleaned data outputs (customers, orders, rfm_segments, segment_summary)
- `charts/` — 4 PNG visualizations
- `data_quality_log.txt` — auditable list of every cleaning decision made
- `summary_stats.txt` — headline numbers

## How to talk about this in an interview
- **"Walk me through your process"** → Start with the business question, not the code. Then: clean → validate →
  segment → visualize → recommend.
- **"Why RFM and not just total spend?"** → Total spend alone hides a customer who spent a lot once, 2 years ago,
  vs. one who orders reliably every month. Recency and frequency catch churn risk that monetary value alone misses.
- **"What would you actually do with the 'At Risk' segment?"** → Propose a targeted win-back email/discount,
  and describe how you'd measure success (compare reactivation rate vs. a control group — ties into A/B testing,
  see Project 2).
- **"What's a limitation of this analysis?"** → RFM quartiles are relative to this dataset — thresholds should be
  revisited as the business grows, and it doesn't account for product margin, only revenue.
