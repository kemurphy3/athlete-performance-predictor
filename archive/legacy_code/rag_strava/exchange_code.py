# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:44:53 2025

@author: kemur
"""

import requests

CLIENT_ID = ""
CLIENT_SECRET = ""  
CODE = ""

res = requests.post(
    url="https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": CODE,
        "grant_type": "authorization_code"
    }
)

print(res.json())
