# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:51:45 2025

@author: kemur
"""

import json
import os
from datetime import datetime
import pandas as pd

INPUT_FILE = "C:/Users/kemur/athlete-performance-predictor/data/strava_activities.json"
activities_txt_list = "C:/Users/kemur/athlete-performance-predictor/data/strava_activities_by_date.txt"
activities_csv = "C:/Users/kemur/athlete-performance-predictor/data/activities.csv"

def load_activities(path):
    with open(path, "r") as f:
        return json.load(f)

def meters_to_miles(meters):
    return round(meters / 1609.34, 2)

def seconds_to_pace(seconds, distance_mi):
    if distance_mi == 0:
        return "N/A"
    pace_sec = seconds / distance_mi
    minutes = int(pace_sec // 60)
    seconds = int(pace_sec % 60)
    return f"{minutes}:{seconds:02d} per mile"

def format_activity(activity):
    date_str = activity["start_date_local"].replace("Z", "")
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
    type_ = activity["type"]
    dist = meters_to_miles(activity.get("distance", 0))
    time_min = round(activity.get("elapsed_time", 0) / 60)
    pace = seconds_to_pace(activity.get("elapsed_time", 0), dist)
    name = activity.get("name", "Unnamed")

    return f"On {date}, I did a {type_} called '{name}' for {dist} miles in {time_min} minutes, averaging {pace}."

def activities_by_date():
    activities = load_activities(INPUT_FILE)
    text_chunks = [format_activity(act) for act in activities]

    with open(activities_txt_list, "w") as f:
        for line in text_chunks:
            f.write(line + "\n")

    print(f"Wrote {len(text_chunks)} activity chunks to {activities_txt_list}")
    
def convert_json_to_csv():
    activities = load_activities(INPUT_FILE)
    rows = []
    for a in activities:
        try:
            date = datetime.strptime(a["start_date_local"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        except:
            date = a["start_date_local"]
        distance_mi = meters_to_miles(a.get("distance", 0))
        elapsed_sec = a.get("elapsed_time", 0)

        rows.append({
            "date": date,
            "name": a.get("name"),
            "type": a.get("type"),
            "distance_miles": distance_mi,
            "duration_min": round(elapsed_sec / 60, 1),
            "pace_per_mile": seconds_to_pace(elapsed_sec, distance_mi)
        })
    df = pd.DataFrame(rows)
    df.to_csv(activities_csv, index=False)
    print(f"Saved {len(df)} rows to {activities_csv}")

if __name__ == "__main__":
    activities_by_date()
    convert_json_to_csv()
