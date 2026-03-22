import mysql.connector
import os
import logging
from dotenv import load_dotenv

# Explicitly load env variables here so db.py can run independently if needed
load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"), 
        user=os.getenv("DB_USER", "root"), 
        password=os.getenv("DB_PASSWORD", ""), 
        database=os.getenv("DB_NAME", "triage_db")
    )

def init_db():
    """Initializes the database and required tables if they do not exist."""
    try:
        # 1. Connect without specifying the database to ensure the DB itself exists
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"), 
            user=os.getenv("DB_USER", "root"), 
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = conn.cursor()
        db_name = os.getenv("DB_NAME", "triage_db")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()

        # 2. Connect to the specific database to create tables
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(255),
            role VARCHAR(50) DEFAULT 'doctor'
        )
        """)

        # Create Reports Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id VARCHAR(50),
            patient_name VARCHAR(100),
            age INT,
            gender VARCHAR(10),
            disease_name VARCHAR(100),
            file_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Success: Database initialized successfully.")
        
    except Exception as e:
        logging.error(f"Error initializing database: {e}")