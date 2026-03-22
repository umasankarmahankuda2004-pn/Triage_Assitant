from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from db import get_db_connection
import pdfplumber
import requests
import os
from functools import lru_cache
import logging

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

analysis_bp = Blueprint("analysis", __name__)

@analysis_bp.before_request
def require_doctor_login():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("signin"))
    if session.get("role") != "doctor":
        flash("Unauthorized Access")
        return redirect(url_for("signin"))

# ==========================
# FETCH REPORTS
# ==========================
def get_patient_reports(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reports WHERE patient_id=%s", (patient_id,))
    data = cursor.fetchall()

    conn.close()
    return data


# ==========================
# PDF TEXT EXTRACTION
# ==========================
@lru_cache(maxsize=50)
def _extract_text_from_file(path, max_chars=4000):
    """Caches extracted text per file to prevent redundant slow disk/PDF operations."""
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Early exit: Stop parsing if we've already reached the limit
                if len(text) >= max_chars:
                    break
    except Exception as e:
        logging.error(f"PDF Error on {path}: {e}")
    return text

def extract_text_from_pdfs(reports):
    text = ""

    for report in reports:
        # Prepend the upload folder since the DB only stores the filename
        path = os.path.join("static/uploads", report["file_path"])
        text += _extract_text_from_file(path)
        
        # Stop checking other reports if we already have enough context
        if len(text) >= 4000:
            break

    return text[:4000]   # limit text


# ==========================
# OLLAMA CALL
# ==========================
def call_ollama(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:8b",  # 🔥 switched to Llama 3 for better instruction following
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        data = response.json()

        return data.get("response", "No response")

    except Exception as e:
        return "AI Error: " + str(e)


# ==========================
# 🚨 EMERGENCY DETECTOR
# ==========================
RED_FLAGS = {
    "chest pain", "breathing problem", "unconscious",
    "bleeding", "heart attack", "stroke", "severe pain"
}

def detect_emergency(text):
    text = text.lower()
    return any(flag in text for flag in RED_FLAGS)


# ==========================
# ANALYSIS ROUTE
# ==========================
@analysis_bp.route("/analysis", methods=["GET", "POST"])
def analysis():
    patient = None
    summary = None
    triage = None

    if request.method == "POST":
        patient_id = request.form["patient_id"]
        reports = get_patient_reports(patient_id)

        if reports:
            patient = {
                "patient_id": reports[0]["patient_id"],
                "name": reports[0]["patient_name"],
                "age": reports[0]["age"],
                "gender": reports[0]["gender"],
                "disease": reports[0]["disease_name"]
            }

            text = extract_text_from_pdfs(reports)

            prompt = f"""
You are a medical AI.

Return STRICTLY:

Triage: Emergency / Moderate / Normal

Also give:
- Summary
- Abnormal findings
- Risk level

Patient Data:
{text}
"""
            summary = call_ollama(prompt)

            if "emergency" in summary.lower():
                triage = "Emergency"
            elif "moderate" in summary.lower():
                triage = "Moderate"
            else:
                triage = "Normal"

        else:
            summary = "No data found"

    return render_template("analysis.html",
                           patient=patient,
                           summary=summary,
                           triage=triage)


# ==========================
# 💬 CHAT ROUTE (REAL TRIAGE)
# ==========================
@analysis_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json

    patient_id = data.get("patient_id")
    question = data.get("question")
    history = data.get("history", [])

    if not patient_id or not question:
        return jsonify({"reply": "Missing data"})

    reports = get_patient_reports(patient_id)

    if not reports:
        return jsonify({"reply": "No patient data found"})

    text = extract_text_from_pdfs(reports)

    # 🧠 Build conversation
    convo = ""
    for h in history:
        convo += f"{h['role']}: {h['content']}\n"

    # 🔥 REAL TRIAGE PROMPT
    prompt = f"""
You are an Emergency Room triage assistant.

Rules:
- Ask ONLY ONE question at a time
- Keep response under 15 words
- Be direct like a doctor
- No explanations

Emergency signs:
chest pain, breathing issue, unconscious, heavy bleeding

Conversation:
{convo}

Patient Report:
{text}

User:
{question}

Response:
"""

    reply = call_ollama(prompt)

    return jsonify({"reply": reply})