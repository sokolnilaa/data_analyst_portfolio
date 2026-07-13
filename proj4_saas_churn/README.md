# Project 4: SaaS Subscription Churn & Retention Analysis

## Business question
"What's our churn rate, is it getting better or worse, which customers are most likely to leave,
and what's each subscription plan actually worth to us over its lifetime?"

## Data
`saas_subscriptions.csv` — 3,000 subscription records (2022-2024): plan tier, MRR, signup/churn dates,
engagement metrics (logins, support tickets, NPS). *(Synthetic, with churn probability deliberately tied to
real engagement signals — low usage, low NPS, high support-ticket volume — rather than random, so the
statistical tests below have genuine signal to find, the same as a real product-usage dataset would.)*

## What I did
1. **Cleaned the data** — removed duplicates; explicitly *did not* impute the 25% of missing NPS scores
   (survey non-response is itself informative — imputing sentiment risks hiding a real pattern, e.g. unhappy
   customers may be less likely to respond at all).
2. **Built a monthly MRR & logo churn rate trend** — tracks revenue and the % of customers churning each month
   in one view, so you can see if a "good" MRR month is being propped up by new signups masking rising churn.
3. **Cohort retention analysis** — % of each signup cohort still subscribed N months later.
4. **Churn driver testing** — chi-square tests for plan/channel, t-tests for engagement metrics (logins,
   tickets, NPS) comparing churned vs. active customers.
5. **LTV estimate by plan** — using the standard SaaS approximation `LTV ≈ Average MRR / Monthly Churn Rate`.

## Key findings
- **Current MRR: £216,251**; average monthly logo churn rate: **2.94%** — roughly in line with healthy
  SMB SaaS benchmarks (2-3%/month), Enterprise well below that.
- **Plan and acquisition channel both significantly affect churn** (chi-square, p<0.001) — Enterprise churns
  far less than Basic; Sales-led signups are stickier than Paid Ads.
- **Engagement is a real churn signal, not just correlation with plan**: churned customers logged in less
  (8.2 vs 9.0 sessions/month), opened more support tickets (1.27 vs 1.13), and had lower NPS (33.7 vs 36.7) —
  all statistically significant (p<0.01).
- **LTV varies enormously by plan**: Enterprise ≈ **£37,142**, Pro ≈ **£2,864**, Basic ≈ **£899**. This is the
  number that should drive CAC targets — if Sales/Marketing is spending the same to acquire a Basic customer
  as an Enterprise one, that's a resource misallocation worth flagging.

## Files
- `generate_data.py` — synthetic data generator
- `analysis.py` — cleaning, MRR/churn trend, cohort retention, churn-driver tests, LTV calculation
- `data/` — cleaned data + `mrr_trend.csv`, `chi_square_results.csv`, `t_test_results.csv`, `ltv_by_plan.csv`
- `charts/` — 4 PNG visualizations (MRR & churn trend, cohort retention heatmap, engagement boxplots, LTV by plan)
- `data_quality_log.txt`, `summary_stats.txt`

## How to talk about this in an interview
- **"Walk me through the LTV formula — why divide by churn rate?"** → `1 / monthly churn rate` estimates average
  customer lifetime in months (e.g., 3% monthly churn ≈ 33 months average lifetime). Multiply by average MRR to
  get lifetime value. It's a simplification (assumes constant churn rate and MRR over time) — good to say that
  out loud rather than present it as exact.
- **"Why didn't you impute the missing NPS scores?"** → Good analysts know *when not* to impute. Missingness in
  survey data is often non-random (unhappy or disengaged customers skip surveys), so filling it with a median
  would quietly erase a real signal. I'd rather flag it as a limitation than fabricate certainty.
- **"How would you act on the engagement findings?"** → Propose a proactive intervention: flag accounts with
  low logins + open support tickets as "at risk" and trigger a customer-success outreach, rather than waiting
  for a cancellation.
- **"What's a limitation of this analysis?"** → It's observational — low engagement predicts churn, but we
  can't be certain low engagement *causes* churn versus both being symptoms of a customer who was a poor fit
  from the start. Also, MRR churn (revenue-weighted) can tell a different story than logo churn (customer-count) —
  worth computing both and comparing, especially since Enterprise customers being few but valuable can swing
  MRR churn very differently from logo churn.
