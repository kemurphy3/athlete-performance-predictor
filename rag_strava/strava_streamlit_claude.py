import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatAnthropic
from typing import List, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# --- CONFIG ---
DATA_DIR = os.getenv("DATA_DIR", "../data")
JSON_PATH = os.path.join(DATA_DIR, "strava_activities.json")
CSV_PATH = os.path.join(DATA_DIR, "activities.csv")

# --- DATA FETCHING ---
def fetch_strava_activities(force: bool = False) -> None:
    """Fetch Strava activities and save to JSON if missing or stale."""
    import fetch_strava_data as fsd
    try:
        fsd.safe_fetch_activities(force=force)
    except Exception as e:
        st.error(f"Failed to fetch Strava data: {e}")
        raise

# --- DATA PREPROCESSING ---
def preprocess_activities() -> pd.DataFrame:
    """Convert JSON to CSV and return DataFrame."""
    import preprocess_strava as pps
    try:
        pps.convert_json_to_csv()
        df = pd.read_csv(CSV_PATH)
        return df
    except Exception as e:
        st.error(f"Failed to preprocess Strava data: {e}")
        raise

# --- TEXT CHUNKING ---
def make_text_chunks(df: pd.DataFrame) -> List[str]:
    """Convert DataFrame rows to text chunks for retrieval."""
    try:
        texts = [
            f"Date: {row['date']}, Type: {row['type']}, Distance: {row['distance_miles']} mi, "
            f"Time: {row['duration_min']} min, Avg Pace: {row['pace_per_mile']}"
            for _, row in df.iterrows()
        ]
        return texts
    except Exception as e:
        st.error(f"Failed to create text chunks: {e}")
        raise

# --- VECTORSTORE ---
@st.cache_resource(show_spinner=False)
def build_vectorstore(text_chunks: List[str]):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = splitter.create_documents(text_chunks)
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(docs, embedding=embeddings)
        return vectorstore
    except Exception as e:
        st.error(f"Failed to build vectorstore: {e}")
        raise

# --- LLM SETUP ---
def get_claude_llm() -> ChatAnthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set in environment.")
        raise ValueError("Missing Claude API key.")
    try:
        llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=512,
            anthropic_api_key=api_key
        )
        return llm
    except Exception as e:
        st.error(f"Failed to initialize Claude LLM: {e}")
        raise

# --- QA CHAIN ---
def build_qa_chain(vectorstore) -> RetrievalQA:
    try:
        llm = get_claude_llm()
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            chain_type="stuff"
        )
        return qa_chain
    except Exception as e:
        st.error(f"Failed to build QA chain: {e}")
        raise

# --- STREAMLIT UI ---
def main():
    st.set_page_config(page_title="Strava Claude Chatbot", page_icon="🏃‍♀️")
    st.title("🏃‍♀️ Strava Training Chatbot (Claude)")
    st.markdown("Ask anything about your Strava activities!")

    # Data loading and processing
    with st.spinner("Loading and processing your Strava data..."):
        try:
            fetch_strava_activities()
            df = preprocess_activities()
            text_chunks = make_text_chunks(df)
            vectorstore = build_vectorstore(text_chunks)
            qa_chain = build_qa_chain(vectorstore)
        except Exception:
            st.stop()

    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask something about your runs:", key="user_input")
    if st.button("Send") or user_input:
        if user_input:
            with st.spinner("Thinking..."):
                try:
                    answer = qa_chain.run(user_input)
                    st.session_state.chat_history.append((user_input, answer))
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display chat history
    for q, a in st.session_state.chat_history:
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Claude:** {a}")

if __name__ == "__main__":
    main() 