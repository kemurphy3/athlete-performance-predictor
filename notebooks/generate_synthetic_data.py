import pandas as pd
import numpy as np

np.random.seed(42)
days = pd.date_range("2025-06-01", "2025-07-01")
n = len(days)

data = pd.DataFrame({
    "date": days,
    "distance_km": np.random.normal(6, 2, n).clip(3, 15),
    "pace": np.random.normal(5.5, 0.5, n).clip(4.5, 7),
    "avg_hr": np.random.normal(150, 10, n),
    "sleep_hours": np.random.normal(7.2, 0.8, n),
    "hrv": np.random.normal(60, 10, n),
    "rpe": np.random.randint(3, 9, n),
    "soreness": np.random.randint(1, 5, n),
    "age": 33,
    "temp_c": np.random.normal(24, 5, n),
    "humidity": np.random.normal(55, 15, n),
    "wind_kph": np.random.normal(12, 4, n),
})

data["race_pace"] = (
    data["pace"]
    + 0.05 * (70 - data["hrv"])
    + 0.03 * (data["temp_c"] - 22)
    + 0.04 * (data["soreness"])
    + np.random.normal(0, 0.2, n)
)

data.to_csv("C:/Users/kemur/athlete-performance-predictor/data/raw/synthetic_athlete_data.csv", index=False)
print("✅ Synthetic data saved to data/raw/")
 
