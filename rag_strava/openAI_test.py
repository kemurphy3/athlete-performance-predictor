# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 15:30:25 2025

@author: kemur
"""

from dotenv import load_dotenv
import os
import openai

load_dotenv()  # This loads variables from .env into the environment

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)