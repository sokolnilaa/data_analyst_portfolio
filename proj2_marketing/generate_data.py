"""
Generates two realistic (synthetic) marketing datasets:
1. channel_performance.csv - daily spend/impressions/clicks/conversions per channel (6 months)
2. ab_test_checkout.csv - a checkout-page A/B test (control vs. new design), user-level conversion data
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)

# ---------------- 1. CHANNEL PERFORMANCE ----------------
channels = {
    # channel: (base_daily_spend, CTR range, CVR range, cost_variability)
    "Paid Search":  (450, (0.035, 0.06), (0.03, 0.05)),
    "Paid Social":  (600, (0.015, 0.03), (0.015, 0.03)),
    "Email":        (50,  (0.08, 0.15), (0.05, 0.09)),
    "Affiliate":    (300, (0.02, 0.04), (0.02, 0.035)),
    "Display":      (350, (0.005, 0.015), (0.005, 0.015)),
}

dates = pd.date_range("2024-01-01", "2024-06-30", freq="D")
rows = []
for date in dates:
    weekday_factor = 1.15 if date.weekday() < 5 else 0.8  # weekdays perform better (B2B-ish product)
    for ch, (base_spend, ctr_range, cvr_range) in channels.items():
        spend = max(0, rng.normal(base_spend, base_spend * 0.2)) * weekday_factor
        cpm = rng.uniform(4, 14)
        impressions = int((spend / cpm) * 1000)
        ctr = rng.uniform(*ctr_range)
        clicks = int(impressions * ctr)
        cvr = rng.uniform(*cvr_range)
        conversions = int(clicks * cvr)
        revenue_per_conv = rng.uniform(35, 95)
        revenue = conversions * revenue_per_conv
        rows.append({
            "date": date, "channel": ch, "spend": round(spend, 2),
            "impressions": impressions, "clicks": clicks,
            "conversions": conversions, "revenue": round(revenue, 2),
        })

channel_perf = pd.DataFrame(rows)

# inject a few missing spend values (finance export gaps) and one duplicated day (system glitch)
channel_perf.loc[channel_perf.sample(frac=0.01, random_state=1).index, "spend"] = np.nan
dupe_day = channel_perf[channel_perf["date"] == "2024-03-15"]
channel_perf = pd.concat([channel_perf, dupe_day], ignore_index=True)

channel_perf.to_csv("data/channel_performance.csv", index=False)

# ---------------- 2. A/B TEST: CHECKOUT REDESIGN ----------------
n_control = 5200
n_treatment = 5150

# true underlying conversion rates (treatment genuinely better, but not huge - realistic effect size)
p_control = 0.086
p_treatment = 0.101

control = pd.DataFrame({
    "user_id": [f"U{i}" for i in range(n_control)],
    "group": "control",
    "converted": rng.binomial(1, p_control, n_control),
    "device": rng.choice(["mobile", "desktop", "tablet"], n_control, p=[0.62, 0.33, 0.05]),
    "session_duration_sec": np.round(rng.gamma(2, 60, n_control), 1),
})
treatment = pd.DataFrame({
    "user_id": [f"U{i+n_control}" for i in range(n_treatment)],
    "group": "treatment",
    "converted": rng.binomial(1, p_treatment, n_treatment),
    "device": rng.choice(["mobile", "desktop", "tablet"], n_treatment, p=[0.62, 0.33, 0.05]),
    "session_duration_sec": np.round(rng.gamma(2.2, 62, n_treatment), 1),
})

ab_test = pd.concat([control, treatment], ignore_index=True).sample(frac=1, random_state=2).reset_index(drop=True)
ab_test.to_csv("data/ab_test_checkout.csv", index=False)

print("channel_performance:", channel_perf.shape)
print("ab_test_checkout:", ab_test.shape)
print(ab_test.groupby("group")["converted"].mean())
