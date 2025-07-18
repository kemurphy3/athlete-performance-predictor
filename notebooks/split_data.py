import pandas as pd
from sklearn.model_selection import train_test_split

rootDir = "C:/Users/kemur/athlete-performance-predictor/"
df = pd.read_csv(rootDir + "data/raw/synthetic_athlete_data.csv")
train_df, test_df = train_test_split(df, test_size = 0.2, shuffle = False)

train_df.to_csv(rootDir + "data/processed/train.csv", index = False)
test_df.to_csv(rootDir + "data/processed/test.csv", index = False)
print("Train / test split saved")