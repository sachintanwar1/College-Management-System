"""
config.py – Central configuration for the Advanced Face Attendance System.
Works with the app.py you generated.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class BaseConfig:
    """Base configuration used by Development and Production"""

    # -----------------------------
    # Flask Core Config
    # -----------------------------
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    SESSION_COOKIE_NAME = "face_attendance_session"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

    # -----------------------------
    # Paths (auto-created by app.py)
    # -----------------------------
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")
    TEACHER_FACE_DIR = os.path.join(UPLOADS_DIR, "teacher_faces")
    STUDENT_FACE_DIR = os.path.join(UPLOADS_DIR, "student_faces")

    # JSON/DB files
    STUDENT_DB = os.path.join(DATA_DIR, "students.json")
    TEACHER_DB = os.path.join(DATA_DIR, "teachers.json")
    SESSIONAL_MARKS_DB = os.path.join(DATA_DIR, "sessional_marks.json")
    SEMESTER_RESULTS_DB = os.path.join(DATA_DIR, "semester_results.json")

    # -----------------------------
    # Database (SQLite by default)
    # -----------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.sqlite3"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------
    # File Upload Settings
    # -----------------------------
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
    MAX_IMAGE_SIZE_MB = 5  # optional soft limit

    # -----------------------------
    # Face Recognition Settings
    # -----------------------------
    FACE_DETECTION_MODEL = "hog"  # options: 'hog' or 'cnn'
    FACE_MATCH_THRESHOLD = 0.45   # lower = stricter (0.35–0.6 recommended)
    EMBEDDINGS_MODEL = "facenet"  # or 'dlib', 'torch', your custom model

    # -----------------------------
    # PDF Rendering
    # -----------------------------
    ENABLE_PDF_EXPORT = True
    WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")
    PDFKIT_CONFIG = None  # Will be initialized in app.py if available

    # -----------------------------
    # Logging
    # -----------------------------
    LOG_LEVEL = "DEBUG"

    # -----------------------------
    # Teacher Upload Protection
    # -----------------------------
    ADMIN_UPLOAD_KEY = os.environ.get("ADMIN_UPLOAD_KEY", "admin123")  # demo only


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"
    FACE_MATCH_THRESHOLD = 0.50  # more relaxed during testing


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    # In production always override SECRET_KEY + DB via environment variables
    FACE_MATCH_THRESHOLD = 0.42  # more strict in production
