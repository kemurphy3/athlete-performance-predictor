# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 11:08:53 2025

@author: kemur
"""

#from patched_hf_endpoint import PatchedHuggingFaceEndpoint as HuggingFaceEndpoint
#from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_huggingface import HuggingFaceEndpoint
import os
from dotenv import load_dotenv

load_dotenv()

#callbacks = [StreamingStdOutCallbackHandler()]

# llm = HuggingFaceEndpoint(
#     #endpoint_url="http://localhost:8010/",
#     repo_id="google/flan-t5-base",
#     task="text2text-generation",
#     temperature=0.01,
#     max_new_tokens=512,
#     #streaming=False,
#     #callbacks=[StreamingStdOutCallbackHandler()],
#     huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
# )

llm = HuggingFaceEndpoint(
    repo_id="google/flan-t5-large",
    task="text2text-generation",
    temperature=0.01,
    max_new_tokens=512,
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
)


print(llm.invoke("What is Deep Learning?"))
