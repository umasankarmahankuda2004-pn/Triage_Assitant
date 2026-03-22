# 🏥 Triage Assistant - Project Overview

**Triage Assistant** is an AI-powered medical web application designed to streamline hospital or clinic workflows. It bridges the gap between lab processing and doctor consultations by automatically analyzing patient reports, detecting medical emergencies, and providing AI-driven triage summaries.

The application is built with privacy in mind, utilizing a locally hosted Large Language Model (Ollama) to ensure that sensitive patient medical data never leaves the local network.

---

## 👥 User Roles & Workflows

The system uses Role-Based Access Control (RBAC) to separate responsibilities:

### 1. Lab Technicians (`lab_tech`)

- **Workflow:** Lab technicians log in to their specific dashboard to register new patient data.
- **Capabilities:** They fill out patient details (Name, Age, Gender, Disease) and securely upload medical reports in **PDF format**. The files are saved locally to `static/uploads`, and the metadata is tracked in the database.

### 2. Doctors (`doctor`)

- **Workflow:** Doctors log in to a dedicated dashboard where they can oversee patient cases.
- **Capabilities:**
  - **View Reports:** Browse or search through a history of uploaded patient reports.
  - **AI Analysis:** Select a patient to instantly receive an AI-generated summary, abnormal findings, risk level, and a Triage status (Normal, Moderate, or Emergency).
  - **AI Chat:** Doctors can interact with an AI chat assistant to ask specific questions about a patient's report (e.g., "What is the patient's blood pressure?"). The AI behaves like a direct, concise ER triage assistant.

---

## ✨ Key Features

- **Local AI Triage & Summarization:** Connects to a local instance of Ollama (specifically running `llama3:8b`) to read medical texts and provide structured analysis without sending patient data to third-party cloud APIs like OpenAI.
- **Instant Emergency Detection:** A hard-coded emergency scanner immediately flags critical keywords (e.g., "chest pain", "heart attack", "unconscious") to alert the doctor before the AI even finishes generating its response.
- **Smart PDF Parsing & Caching:** Uses `pdfplumber` to extract text from medical documents. To ensure the application remains fast, it utilizes Python's `@lru_cache`, which remembers the text of recently opened PDFs so the server doesn't have to re-read the disk during a chat session.
- **Secure Authentication:** Implements secure user registration and login using Werkzeug's password hashing (`generate_password_hash`, `check_password_hash`) and session management.
- **Production-Ready Security:** Includes a 16MB file upload limit to prevent Denial of Service (DoS) attacks, restricts uploads strictly to PDFs, and disables Flask debug mode in production via environment variables.

---

## 🛠️ Technology Stack

- **Backend:** Python, Flask (using Blueprints for modular routing)
- **Database:** MySQL (configured via `mysql-connector-python` and automatically initialized via `db.py`)
- **AI/LLM:** Ollama (`llama3:8b` model) interacting via HTTP requests
- **Document Processing:** `pdfplumber` for text extraction from PDFs
- **Frontend:** HTML5, Jinja2 Templating, and Bootstrap 5 for responsive design
- **Environment Management:** `python-dotenv` for securely loading credentials
- **Deployment:** Pre-configured for deployment using `gunicorn` (WSGI server)

---

## 📂 Architecture Highlights

- **`app.py`**: The main entry point. Handles app initialization, security configurations, global database setup, authentication routes, and blueprint registration.
- **`db.py`**: Manages the MySQL connection and contains an `init_db()` function that automatically creates the `triage_db` database, `users` table, and `reports` table on startup.
- **`analysis.py`**: The core AI engine. Handles routing for doctors, extracts text from PDFs with early-exit limits (up to 4,000 chars), constructs prompts, and communicates with Ollama.
- **`report_upload.py`**: The lab technician's module for handling form data and securely saving PDF files to the local file system.
