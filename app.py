import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

# ================= CONFIG =================
st.set_page_config(page_title="TheraLink AI", page_icon="🧠", layout="wide")

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
st.sidebar.title("🧠 TheraLink AI")
role = st.sidebar.radio("Select Role", ["Patient", "Doctor"])

# =====================================================
# ===================== PATIENT =======================
# =====================================================
if role == "Patient":
    st.title("📝 Daily Mental Health Check-In")

    patient_id = st.text_input("Patient ID", value="patient_001")

    responses = []
    for q in QUESTIONS:
        responses.append(st.slider(q, 1, 5, 3))

    st.markdown("### 💬 Express Your Feelings")
    patient_text = st.text_area(
        "Describe your emotions and thoughts today...",
        height=150
    )

    # Emergency notice
    if "suicide" in patient_text.lower():
        st.error("If you are in immediate danger, contact emergency services immediately.")

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

        st.line_chart(history.set_index("Date")["Score"])
        st.metric("Wellness Score", latest_score)

        st.markdown("### Patient Narrative")
        st.write(latest_text if latest_text else "No narrative provided.")

        # ================= AI CRITICAL REPORT =================
        st.markdown("### 🧠 AI Clinical Risk & Criticality Report")

        def get_model():
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

        model_name = get_model()

        if not model_name:
            st.error("No compatible Gemini model available.")
        else:
            model = genai.GenerativeModel(model_name.replace("models/", ""))

            prompt = f"""
You are a clinical suicide risk and behavioral assessment AI assisting a licensed psychiatrist.

Analyze the patient data carefully.

Current Wellness Score (1–5): {latest_score}
Historical Scores: {trend_scores}
Behavioral Metrics: {latest_responses}

Patient Narrative:
{latest_text if latest_text.strip() else "No narrative provided."}

Generate a structured professional clinical report including:

1. Current Psychological Condition
2. Suicide/Self-Harm Risk Level (Low / Moderate / High / Critical)
3. Severity Assessment
4. Immediate Risk Indicators
5. Possible Short-Term Outcomes if Unaddressed
6. Clinical Attention Priorities
7. Professional Hints for the Treating Doctor

Rules:
- Clearly classify severity if suicidal ideation is present.
- Use firm clinical tone.
- Do NOT give treatment advice to patient.
"""

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.15,
                    "max_output_tokens": 900
                }
            )

            st.write(response.text)

        st.markdown("### Doctor Notes")
        pdata["notes"] = st.text_area(
            "Clinical session notes",
            value=pdata.get("notes", ""),
            height=150
        )
