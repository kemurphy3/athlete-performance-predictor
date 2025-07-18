# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:44:53 2025

@author: kemur
"""

import requests

CLIENT_ID = "168662"
CLIENT_SECRET = "da9f34a81775617c2d45ec0f4339a7609b8054f4"  
CODE = "603dfd4bd67575b89aa52f32f0a25efd79863aaa"

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
