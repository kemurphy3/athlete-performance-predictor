# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 21:17:11 2025

@author: kmurph
"""

import requests
import os
import json
import pandas as pd
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
#from langchain.llms import HuggingFaceHub
#from langchain_community.llms import HuggingFaceEndpoint
from langchain_huggingface.llms import HuggingFaceEndpoint
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import streamlit as st
import fetch_strava_data as fsd
import preprocess_strava as pps
from dotenv import load_dotenv
load_dotenv()

# Pull data from Strava API
#fetch_activities()
print("Pulling data from Strava")
fsd.safe_fetch_activities()

# Upload strava data and organize 
pps.convert_json_to_csv()
df = pd.read_csv(r"C:\Users\kemur\athlete-performance-predictor\data\activities.csv")
texts = []

for _, row in df.iterrows():
    #txt = f"Date: {row['Activity Date']}, Type: {row['Activity Type']}, Distance: {row['Distance']} mi, Time: {row['Elapsed Time']}, Avg Pace: {row['Average Pace']}"
    txt = f"Date: {row['date']}, Type: {row['type']}, Distance: {row['distance_miles']} mi, Time: {row['duration_min']}, Avg Pace: {row['pace_per_mile']}"

    texts.append(txt)
    
# Split and embed
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
docs = text_splitter.create_documents(texts)
print("Docs: ", docs)
#docs_small = docs[:5]
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = FAISS.from_documents(docs, embedding)

# # Set up QA
# qa = RetrievalQA.from_chain_type(
#     llm=OpenAI(temperature=0),
#     retriever=db.as_retriever()
# )

# Set up access to LLM
print("Establishing connection to LLM")
llm = HuggingFaceEndpoint(
    # repo_id="google/flan-ul2",
    # task="text2text-generation",
    repo_id="google/flan-t5-base",
    task="text2text-generation",
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    temperature=0.3,
    max_new_tokens=128,
)



qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=db.as_retriever(),
    chain_type="stuff"
)



if __name__ == "__main__":
    # Ask an initial question
    query = {"query": "What was my longest run in June?"}
    response = qa.invoke(query)
    print("Answer:", response["result"])

    # Interactive loop
    while True:
        user_input = input("Ask a question about your training (or type 'exit'): ")
        if user_input.lower() in ["exit", "quit"]:
            break
        result = qa.invoke({"query": user_input})
        print("Answer:", result["result"])


    
st.title("Training RAG Chatbot")
q = st.text_input("Ask about your performance data:")
if q:
    st.write(qa.invoke(q))