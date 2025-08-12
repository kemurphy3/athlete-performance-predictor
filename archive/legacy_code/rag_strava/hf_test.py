# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 11:45:34 2025

@author: kemur
"""

from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()

client = InferenceClient(  # connects to free serverless API :contentReference[oaicite:2]{index=2}
    model="google/flan-t5-base",  # supported for inference API
    token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
)

response = client.text_generation("What is Deep Learning?")
print(response)  # prints the full answer

