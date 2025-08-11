# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 12:12:21 2025

@author: kemur
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

#input_text = "Translate English to French: Hello, how are you?"
input_text = "Who won the 2023 Women's World Cup for soccer?"
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
