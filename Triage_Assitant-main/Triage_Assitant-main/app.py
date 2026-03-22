from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from db import get_db_connection, init_db
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from dotenv import load_dotenv
from report_upload import report_upload_bp
from view_report import view 
from analysis import analysis_bp

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-default-key-change-in-prod")

# 🛡️ Industry Standard: Limit upload size to prevent DoS attacks (16MB max)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Database Tables automatically on startup
init_db()


# ==============================
# LOGIN REQUIRED DECORATOR
# ==============================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first")
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return wrapper


# ==============================
# ROLE REQUIRED DECORATOR
# ==============================
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" not in session or session["role"] != role:
                flash("Unauthorized Access")
                return redirect(url_for("signin"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ==============================
# HOME
# ==============================
@app.route("/")
def home():
    return redirect(url_for("signin"))


# ==============================
# SIGNUP
# ==============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form.get("role", "lab_tech")

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("signup"))

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            flash("Email already registered")
            return redirect(url_for("signup"))

        cursor.execute("SELECT MAX(user_id) AS max_id FROM users")
        result = cursor.fetchone()
        new_id = 1 if result["max_id"] is None else result["max_id"] + 1
        
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (user_id, first_name, last_name, email, password, role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (new_id, first_name, last_name, email, hashed_password, role))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully!")
        return redirect(url_for("signin"))

    return render_template("signup.html")


# ==============================
# SIGNIN
# ==============================
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["role"] = user["role"]
            session["name"] = user["first_name"]

            if user["role"] == "lab_tech":
                return redirect(url_for("lab_dashboard"))
            elif user["role"] == "doctor":
                return redirect(url_for("doctor_dashboard"))
        else:
            flash("Invalid email or password")

    return render_template("signin.html")


# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("signin"))


# ==============================
# LAB DASHBOARD
# ==============================
@app.route("/lab")
@login_required
@role_required("lab_tech")
def lab_dashboard():
    return render_template("labindex.html")


# ==============================
# DOCTOR DASHBOARD
# ==============================
@app.route("/doctor")
@login_required
@role_required("doctor")
def doctor_dashboard():
    return render_template("doctorindex.html")


# ==============================
# REPORT UPLOAD (BLUEPRINT)
# ==============================
app.register_blueprint(report_upload_bp)


# ==============================
# VIEW REPORTS (DOCTOR)
# ==============================
@app.route("/view_reports")
@login_required
@role_required("doctor")
def view_reports_route():

    reports = view()  

    return render_template("view_report.html", reports=reports)


# ==============================
# ANALYSIS (BLUEPRINT)
# ==============================
app.register_blueprint(analysis_bp)

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    # 🛡️ Industry Standard: Disable debug mode in production based on environment variables
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=debug_mode)