# routes/admin_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os, json
from datetime import datetime
from pathlib import Path

bp = Blueprint("admin", __name__, url_prefix="/admin")

DATA_DIR = os.path.join(Path(__file__).resolve().parents[1], "data")

# ---------- HELPER FUNCTIONS ----------
def _load_json(fname, default=[]):
    p = os.path.join(DATA_DIR, fname)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save_json(fname, data):
    p = os.path.join(DATA_DIR, fname)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------- ADMIN LOGIN ----------


# (other code above...)

@bp.route("/login", methods=["GET", "POST"])
def admin_login():
    """
    Admin login that accepts GET and POST.
    Default dev credentials: admin / admin (use env vars in production)
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
        ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = username
            flash("Logged in successfully", "success")
            # try to redirect to admin.dashboard (blueprint) else fallback to dashboard
            try:
                return redirect(url_for("admin.dashboard"))
            except Exception:
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            # return login page with 401 so client sees failure
            return render_template("login.html"), 401

    # GET -> show login form
    return render_template("login.html")


# ---------- ADMIN LOGOUT ----------
@bp.route("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("admin.admin_login"))

# ---------- ADMIN DASHBOARD ----------
@bp.route("/dashboard")
def dashboard():
    if "admin" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("admin.admin_login"))

    teachers = _load_json("teachers.json", [])
    students = _load_json("students.json", [])
    return render_template("dashboard.html", teachers=teachers, students=students)

# ---------- ADMIN SETTINGS ----------
@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if "admin" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("admin.admin_login"))

    if request.method == "POST":
        flash("Settings saved!", "success")

    return render_template("settings.html")
