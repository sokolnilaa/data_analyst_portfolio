# Data Analyst Portfolio — 4 Projects Sokol Nilas


These 4 projects were chosen to cover the range a data analyst interview typically probes:

| # | Project | Core skill on display |
|---|---------|------------------------|
| 1 | E-Commerce Sales & Customer Segmentation | Data cleaning, RFM segmentation, cohort retention |
| 2 | Marketing Channel ROI & Checkout A/B Test | Business metrics (CAC/ROAS), hypothesis testing, statistical significance |
| 3 | HR Employee Attrition Analysis | Chi-square/t-tests, logistic regression, translating stats into HR recommendations |
| 4 | SaaS Subscription Churn & LTV | Time-based/cohort analysis, churn drivers, LTV modeling |

Together they show: cleaning messy real-world data, descriptive + inferential statistics, a touch of
predictive modeling, and — most importantly — turning numbers into a business recommendation, which is
what actually gets data analysts hired (not just correct code).

## Important note on the data
I generated these datasets synthetically rather than pulling live ones, because I didn't have
internet/download access while building this. **Be upfront about this in the interview if asked** — say
something like: *"I built these datasets synthetically with realistic messiness and genuine underlying
relationships baked in, since I wanted full control over demonstrating specific techniques end-to-end. The
cleaning, statistical testing, and analysis methods are identical to what I'd apply to a live company dataset."*
This is a completely normal and honest thing to say — interviewers respect people who are transparent about
their process far more than people who imply something is other than it is.

If you have time before the interview, I'd strongly recommend swapping in **one real dataset** for at least
one project (e.g., the Olist Brazilian E-Commerce dataset on Kaggle maps almost directly onto Project 1, and
the IBM HR Analytics Attrition dataset maps directly onto Project 3) — same code, real data, and then you can
say "real dataset" without caveats. I can walk you through adapting the scripts to a real CSV if you'd like.

## Structure
Each project folder contains:
- `generate_data.py` — how the dataset was built (skip/replace this if you swap in real data)
- `analysis.py` — the actual analysis: cleaning, statistics, visualizations
- `data/` — resulting CSVs (raw + cleaned + summary tables)
- `charts/` — PNG visualizations, ready to drop into a slide deck
- `README.md` — business question, methodology, findings, and an "how to talk about this in the interview" section
- `data_quality_log.txt` / `summary_stats.txt` — the auditable trail of what was done and found

## General interview prep, on top of the project-specific notes
1. **Always start with the business question, not the code.** Interviewers are testing whether you think
   like an analyst (what decision does this inform?) not just whether you can write pandas.
2. **Know your numbers cold.** For each project, be able to state the 2-3 headline numbers from memory
   without looking at notes.
3. **Have one answer ready for "what would you do with more time/data?"** per project — it's asked constantly.
4. **Practice explaining the A/B test and logistic regression projects to a non-technical person.** The
   ability to translate "p=0.036" or "standardized coefficient" into plain English is often the actual thing
   being evaluated, more than the math itself.
5. **Bring the charts, not just the code.** Have the PNGs ready to screen-share or print — a hiring manager
   engages far more with a clear chart than a wall of code.
