# Project 2: Marketing Channel ROI & Checkout A/B Test Analysis

## Business questions
1. "Which marketing channels are actually making us money, and which should we cut or scale?"
2. "We redesigned the checkout page — did conversion actually improve, or could that just be noise?"

## Data
`channel_performance.csv` — 6 months of daily spend/impressions/clicks/conversions/revenue across 5 channels.
`ab_test_checkout.csv` — 10,350 user-level rows from a checkout redesign experiment (control vs. treatment).
*(Synthetic, generated to reflect realistic channel economics and a realistic, modest experiment effect size —
the same shape of data and analysis you'd get from a real marketing/analytics stack.)*

## What I did
**Channel ROI:**
1. Cleaned duplicate rows and imputed missing spend values (median by channel).
2. Calculated CTR, CVR, CAC, and ROAS per channel.
3. Ranked channels by ROAS and visualized CAC side-by-side (a channel can look cheap per-click but still have a bad CAC).

**A/B test:**
1. Calculated conversion rate for control vs. treatment.
2. Ran a **two-proportion z-test** to check statistical significance (not just "treatment number is bigger").
3. Computed a 95% confidence interval on the lift, and checked for interaction effects by device.

## Key findings
- **Email has by far the best ROAS (~67x)** and lowest CAC — heavily under-invested relative to its efficiency.
- **Display is running at a ROAS of 0.77 — losing money on every £1 spent.** This is the single most actionable
  number in the whole analysis: recommend pausing or heavily restructuring Display spend.
- **Paid Search and Affiliate are solidly profitable** and could absorb reallocated Display budget.
- **The checkout redesign produced a statistically significant lift**: control converted at 9.40%, treatment at
  10.64% — a 13.2% relative lift, p = 0.036 (below the 0.05 threshold), 95% CI on the absolute lift is [0.08%, 2.39%].
  This means: we can be reasonably confident the new design helps, but the true effect could be small (as little
  as 0.08 points) — worth running longer or with more traffic if the business needs a tighter estimate before
  a full rollout.
- No strong interaction effect by device — the redesign helps roughly consistently across mobile/desktop/tablet.

## Files
- `generate_data.py` — synthetic data generator
- `analysis.py` — cleaning, ROI metrics, A/B statistical test
- `data/` — raw data + summary tables
- `charts/` — 5 PNG visualizations (ROAS, CAC, revenue trend, A/B conversion with error bars, A/B by device)
- `ab_test_result.txt` — full statistical test output

## How to talk about this in an interview
- **"Why a z-test and not just comparing the two percentages?"** → Comparing raw percentages can't tell you if
  a 1-point difference is real or just sampling noise. The z-test (or equivalently a chi-square test) gives you
  a p-value, which is what lets you say "I'm confident this isn't chance" rather than "the number is bigger."
- **"What would you recommend to the marketing team?"** → Lead with the Display ROAS finding — it's the clearest,
  most defensible, highest-impact recommendation. Reallocate part of that budget to Email/Paid Search.
- **"How would you decide when to stop an A/B test?"** → Talk about pre-registering a minimum sample size /
  power analysis before starting, rather than peeking at results daily and stopping as soon as p < 0.05
  (which inflates false positive rate — a classic pitfall interviewers like to probe).
- **"What's a limitation here?"** → ROAS treats all revenue as directly attributable to the last channel clicked,
  which overstates channels late in the funnel (like Email) and understates awareness-building channels
  (like Display) — worth mentioning you understand attribution is imperfect, not just accept the raw number.
