import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

# ================= CONFIG =================
st.set_page_config(
    page_title="HeyTherapy",
    page_icon="🧠",
    layout="wide"
)

# Get API key from Streamlit Secrets
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# ================= QUESTIONS =================
QUESTIONS = [
    "Mood stability",
    "Anxiety intensity",
    "Emotional regulation",
    "Irritability",
    "Calmness",
    "Negative thoughts",
    "Overthinking",
    "Focus",
    "Decision difficulty",
    "Thinking clarity",
    "Sleep quality",
    "Sleep satisfaction",
    "Energy",
    "Appetite",
    "Physical tension",
    "Motivation",
    "Social connection",
    "Work/study stress",
    "Feeling overwhelmed",
    "Overall well-being"
]

# ================= SESSION STATE =================
if "patients" not in st.session_state:
    st.session_state["patients"] = {}

# ================= SIDEBAR =================
st.sidebar.title("🧠 HeyTherapy")
role = st.sidebar.radio("Select Role", ["Patient", "Doctor"])
