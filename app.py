import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------- CONFIG --------------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("GOOGLE_API_KEY not found. Check your .env file.")
    st.stop()

genai.configure(api_key=API_KEY)

st.set_page_config(
    page_title="TheraLink AI",
    page_icon="🧠",
    layout="wide"
)

# -------------------- STYLE --------------------
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
.badge-green { color: white; background: #2ecc71; padding: 0.3rem 0.7rem; border-radius: 12px; }
.badge-yellow { color: black; background: #f1c40f; padding: 0.3rem 0.7rem; border-radius: 12px; }
.badge-red { color: white; background: #e74c3c; padding: 0.3rem 0.7rem; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# -------------------- QUESTIONS --------------------
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

# -------------------- SESSION STATE --------------------
if "patients" not in st.session_state:
    st.session_state["patients"] = {}

# -------------------- SIDEBAR --------------------
st.sidebar.title("🧠 TheraLink AI")
role = st.sidebar.radio("Select Role", ["Patient", "Doctor"])

# =====================================================
# ===================== PATIENT =======================
# =====================================================
if role == "Patient":
    st.title("📝 Daily Mental Health Check-In")

    patient_id = st.text_input("Patient ID", value="patient_001")

    responses = []
    progress = st.progress(0)

    for i, q in enumerate(QUESTIONS):
        val = st.slider(q, 1, 5, 3)
        responses.append(val)
        progress.progress((i + 1) / len(QUESTIONS))

    st.markdown("### 💬 Express Your Feelings")
    patient_text = st.text_area(
        "Describe your emotions, stressors, and experiences today...",
        height=150
    )

    if st.button("Submit Check-In"):
        score = round(np.mean(responses), 2)
        date = pd.Timestamp.today().date()

        if patient_id not in st.session_state["patients"]:
            st.session_state["patients"][patient_id] = {
                "history": [],
                "notes": "",
                "verified": False
            }

        st.session_state["patients"][patient_id]["history"].append({
            "Date": date,
            "Score": score,
            "Responses": responses,
            "Text": patient_text
        })

        st.success("Check-in submitted successfully.")

# =====================================================
# ===================== DOCTOR ========================
# =====================================================
if role == "Doctor":
    st.title("🏥 Doctor Dashboard")

    patients = st.session_state["patients"]

    if not patients:
        st.warning("No patient data available.")
    else:
        overview = []

        for pid, pdata in patients.items():
            last = pdata["history"][-1]
            overview.append({
                "Patient ID": pid,
                "Latest Score": last["Score"],
                "Risk": "🔴" if last["Score"] <= 2 else "🟡" if last["Score"] <= 3.5 else "🟢"
            })

        overview_df = pd.DataFrame(overview)
        st.dataframe(overview_df, use_container_width=True)

        selected = st.selectbox("Select Patient", overview_df["Patient ID"])
        pdata = patients[selected]
        history = pd.DataFrame(pdata["history"])

        latest_score = history.iloc[-1]["Score"]
        latest_responses = history.iloc[-1]["Responses"]
        latest_text = history.iloc[-1]["Text"]
        trend_scores = history["Score"].tolist()

        st.markdown("---")

        col1, col2 = st.columns([3,1])

        with col1:
            st.line_chart(history.set_index("Date")["Score"])

        with col2:
            if latest_score <= 2:
                st.markdown("<span class='badge-red'>HIGH RISK</span>", unsafe_allow_html=True)
            elif latest_score <= 3.5:
                st.markdown("<span class='badge-yellow'>MODERATE RISK</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge-green'>LOW RISK</span>", unsafe_allow_html=True)

            st.metric("Wellness Score", latest_score)

        st.markdown("### Patient Narrative")
        st.write(latest_text if latest_text else "No narrative provided.")

        # ================= AI CRITICAL REPORT =================
        st.markdown("### 🧠 AI Clinical Risk & Criticality Report")

        def get_model():
            try:
                models = [
                    m.name for m in genai.list_models()
                    if "generateContent" in m.supported_generation_methods
                ]

                for preferred in [
                    "models/gemini-1.5-flash",
                    "models/gemini-1.5-pro",
                    "models/gemini-pro"
                ]:
                    if preferred in models:
                        return preferred

                return models[0] if models else None
            except:
                return None

        model_name = get_model()

        if not model_name:
            st.error("No compatible Gemini model available.")
        else:
            try:
                model = genai.GenerativeModel(model_name.replace("models/", ""))

                prompt = f"""
You are a clinical suicide risk and behavioral assessment AI assisting a licensed psychiatrist.

Analyze the following patient data carefully.

Current Wellness Score (1–5): {latest_score}
Historical Scores: {trend_scores}
Behavioral Metrics (20 values): {latest_responses}

Patient Narrative:
{latest_text if latest_text.strip() else "No narrative provided."}

Generate a structured professional clinical report including:

1. Current Psychological Condition
2. Suicide/Self-Harm Risk Level (Low / Moderate / High / Critical)
3. Severity Assessment (Explain how critical the current state is)
4. Immediate Risk Indicators
5. Possible Short-Term Outcomes if Unaddressed
6. Clinical Attention Priorities
7. Professional Hints for the Treating Doctor

Rules:
- If suicidal ideation appears, clearly classify severity.
- Use firm clinical tone.
- Do NOT provide treatment instructions to patient.
- Provide actionable insights only for the doctor.
"""

                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.15,
                        "max_output_tokens": 900
                    }
                )

                if hasattr(response, "text") and response.text:
                    st.write(response.text)
                else:
                    st.warning("AI did not return a valid report.")

            except Exception as e:
                st.error(f"AI Generation Error: {e}")

        # ================= DOCTOR CONTROLS =================
        st.markdown("### Clinician Verification")
        verify = st.toggle("Verify AI Report", value=pdata.get("verified", False))
        pdata["verified"] = verify

        if verify:
            st.success("Report Verified")

        st.markdown("### Doctor Notes")
        notes = st.text_area(
            "Clinical session notes",
            value=pdata.get("notes", ""),
            height=150
        )
        pdata["notes"] = notes