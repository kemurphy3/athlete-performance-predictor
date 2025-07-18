# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:30:03 2025

@author: kemur
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load values from .env

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")


def get_access_token():
    response = requests.post(
        url="https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
    )
    if response.status_code != 200:
        raise Exception(f"Token refresh failed: {response.status_code}")
    return response.json()["access_token"]

if __name__ == "__main__":
    get_access_token()
