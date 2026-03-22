import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from db import get_db_connection 

report_upload_bp = Blueprint("report_upload", __name__)

# Upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@report_upload_bp.route("/report_upload", methods=["GET", "POST"])
def report_upload():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("signin"))

    if session.get("role") != "lab_tech":
        flash("Unauthorized Access")
        return redirect(url_for("signin"))

    if request.method == "POST":
        try:
            patient_id = request.form["patient_id"]
            patient_name = request.form["patient_name"]
            age = request.form["age"]
            gender = request.form["gender"]
            disease_name = request.form["disease_name"]
            file = request.files["report_file"]

            if file.filename == "":
                flash("No file selected")
                return redirect(url_for("report_upload.report_upload"))

            if not allowed_file(file.filename):
                flash("Invalid file type. Please upload a PDF file.")
                return redirect(url_for("report_upload.report_upload"))

            # ✅ Secure filename
            original_filename = secure_filename(file.filename)
            filename = f"{uuid.uuid4().hex}_{original_filename}"

            # ✅ Save file to folder
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            # ✅ Store ONLY filename in DB
            cursor.execute("""
                INSERT INTO reports 
                (patient_id, patient_name, age, gender, disease_name, file_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (patient_id, patient_name, age, gender, disease_name, filename))

            conn.commit()

            flash("Report uploaded successfully!")
            return redirect(url_for("report_upload.report_upload"))

        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}")
            return redirect(url_for("report_upload.report_upload"))

    return render_template("reportupload.html")