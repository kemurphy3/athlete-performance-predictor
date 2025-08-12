# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 13:17:39 2025

@author: kemur
"""

# strava_chat.py

import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.chat_models import ChatAnthropic  # Claude-compatible LangChain wrapper

import fetch_strava_data as fsd
import preprocess_strava as pps

load_dotenv()

def load_and_prepare_data():
    fsd.safe_fetch_activities()
    pps.convert_json_to_csv()
    df = pd.read_csv("data/activities.csv")

    texts = [
        f"Date: {row['date']}, Type: {row['type']}, Distance: {row['distance_miles']} mi, "
        f"Time: {row['duration_min']} min, Avg Pace: {row['pace_per_mile']}"
        for _, row in df.iterrows()
    ]

    return texts

def build_qa_chain(text_chunks):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = splitter.create_documents(text_chunks)
    embeddings = FAISS.from_documents(docs, model="all-MiniLM-L6-v2")

    # Claude via LangChain wrapper
    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.1,
        max_tokens=512,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=embeddings.as_retriever(),
        chain_type="stuff"
    )

    return qa_chain

def run_chatbot(qa_chain):
    st.title("🏃‍♀️ Strava Training Chatbot")
    query = st.text_input("Ask something about your runs:")
    if query:
        with st.spinner("Thinking..."):
            result = qa_chain.run(query)
            st.write(result)

if __name__ == "__main__":
    try:
        texts = load_and_prepare_data()
        qa = build_qa_chain(texts)
        run_chatbot(qa)
    except Exception as e:
        st.error(f"Error: {e}")
