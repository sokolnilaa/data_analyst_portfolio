# Project 3: HR Employee Attrition Analysis

## Business question
"We're losing employees — which factors actually predict who leaves, versus which are just noise
HR is chasing? What should we fix first?"

## Data
`hr_employees.csv` — 1,500 employee records: demographics, pay, tenure, satisfaction scores, overtime,
and attrition outcome. *(Synthetic, built with realistic underlying drivers — satisfaction, overtime,
time-since-promotion, pay relative to level — the same structure as IBM's well-known HR attrition dataset,
but generated so I could design in specific, defensible ground-truth relationships to test against.)*

## What I did
1. **Cleaned the data** — removed duplicate employee records, imputed missing satisfaction/distance values.
2. **Chi-square tests** on categorical variables (overtime, department, job level) to check which have a
   statistically significant relationship with attrition.
3. **Independent t-tests** on continuous variables (satisfaction, income, tenure, promotion gap) comparing
   employees who left vs. stayed.
4. **Logistic regression** (standardized coefficients) to rank drivers by relative strength while controlling
   for other variables at once — this catches things univariate tests can miss (e.g., two correlated variables
   competing for the same signal).
5. Visualized attrition rate cuts by department, satisfaction, and overtime, plus a correlation heatmap and a
   "tornado chart" of regression drivers.

## Key findings
- **Overall attrition rate: 29.9%** — high enough to be a real business problem, not statistical noise.
- **Statistically significant drivers (p<0.05):** overtime, job level (chi-square); work-life balance, job
  satisfaction, years since last promotion, and monthly income (t-test).
- **Logistic regression's top 3 drivers**, controlling for everything else at once:
  1. `years_since_last_promotion` — the strongest single predictor. Employees who leave average 5.7 years since
     their last promotion vs. 4.6 for those who stay.
  2. `work_life_balance` — lower scores strongly predict leaving.
  3. `job_satisfaction` — same pattern, independent of work-life balance (both matter, not just one proxying the other).
- **Practical read:** pay is a real factor but it's not the top lever — stalled career progression and
  work-life balance are bigger, and cheaper to act on than an across-the-board raise.

## Files
- `generate_data.py` — synthetic data generator
- `analysis.py` — cleaning, chi-square/t-tests, logistic regression, visualizations
- `data/` — cleaned data + `chi_square_results.csv`, `t_test_results.csv`, `logistic_regression_drivers.csv`
- `charts/` — 5 PNG visualizations
- `data_quality_log.txt`, `summary_stats.txt`

## How to talk about this in an interview
- **"Why chi-square/t-test AND logistic regression — isn't that redundant?"** → No: univariate tests (chi-square,
  t-test) tell you if a variable is related to attrition *on its own*, but don't control for other variables.
  Logistic regression shows relative importance *holding everything else constant* — useful because satisfaction
  and work-life balance are correlated, and you want to know if both matter independently or if one is just
  riding on the other's signal.
- **"How would you turn this into a recommendation for leadership?"** → Lead with the promotion-gap finding —
  it's specific, actionable ("review anyone at 4+ years without a promotion"), and cheaper to fix than a
  blanket pay rise.
- **"Correlation vs. causation — does this prove work-life balance causes people to quit?"** → Be ready for this
  one. It's an observational analysis; it shows a strong statistical association, not proof of causation. To move
  closer to causal, you'd want a natural experiment (e.g., did attrition change after a policy adjusted overtime
  in one department but not another) or a properly randomized intervention.
- **"What would you build next?"** → A model that scores current employees' attrition risk so HR can proactively
  intervene, and an ongoing dashboard tracking these KPIs by department/manager over time rather than a one-off report.
