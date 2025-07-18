# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:24:59 2025

@author: kemur
"""

import requests
import json
import os
import time
from strava_auth import get_access_token

ACCESS_TOKEN = get_access_token()
#print("Access token:", ACCESS_TOKEN)
URL = "https://www.strava.com/api/v3/athlete/activities"

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
params = {"per_page": 50, "page": 1}

def fetch_activities():
    res = requests.get(URL, headers=headers, params=params)
    if res.status_code != 200:
        print("Error response:", res.text) 
        raise Exception(f"Failed to fetch: {res.status_code}")
    data = res.json()
    
    with open("C:/Users/kemur/athlete-performance-predictor/data/strava_activities.json", "w") as f:
        json.dump(data, f, indent=2)
        
DATA_PATH = "C:/Users/kemur/athlete-performance-predictor/data/strava_activities.json"

def safe_fetch_activities(force=False):
    """Fetches data only if file is missing or older than 6 hours."""
    if force or not os.path.exists(DATA_PATH):
        print("No existing data found. Fetching from Strava...")
        fetch_activities()
    else:
        last_modified = os.path.getmtime(DATA_PATH)
        if time.time() - last_modified > 6 * 3600:  # older than 6 hours
            print("Data is stale. Re-fetching from Strava...")
            fetch_activities()
        else:
            print("Using cached Strava data.")

if __name__ == "__main__":
    #fetch_activities()
    safe_fetch_activities()
