import pandas as pd
import numpy as np

np.random.seed(42)
days = pd.date_range("2025-06-01", "2025-07-01")
n = len(days)

# 1 km = 0.621371 miles
km_to_miles = 0.621371

# Generate distance in miles instead of kilometers
distance_miles = np.random.normal(6, 2, n).clip(3, 15) * km_to_miles

# Generate pace in min/km, then convert to min/mile
pace_per_km = np.random.normal(5.5, 0.5, n).clip(4.5, 7)
pace_per_mile = pace_per_km / km_to_miles  # Faster pace in miles

data = pd.DataFrame({
    "date": days,
    "distance_miles": distance_miles,
    "pace": pace_per_mile,  # min/mile
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

# Adjust race pace based on synthetic contributors
data["race_pace"] = (
    data["pace"]
    + 0.05 * (70 - data["hrv"])
    + 0.03 * (data["temp_c"] - 22)
    + 0.04 * (data["soreness"])
    + np.random.normal(0, 0.2, n)
)

data.to_csv("C:/Users/kemur/athlete-performance-predictor/data/raw/synthetic_athlete_data.csv", index=False)
print("✅ Synthetic data with miles and min/mile pace saved.")
