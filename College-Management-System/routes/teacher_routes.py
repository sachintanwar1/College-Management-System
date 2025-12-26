# routes/teacher_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash, current_app
from pathlib import Path
import os, json, csv, io
from datetime import datetime

bp = Blueprint("teacher", __name__, url_prefix="/teacher")

DATA_DIR = os.path.join(Path(__file__).resolve().parents[1], "data")

def _load(fname, default=[]):
    p = os.path.join(DATA_DIR, fname)
    if not os.path.exists(p):
        return default
    try:
        with open(p,"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(fname, obj):
    p = os.path.join(DATA_DIR, fname)
    with open(p,"w",encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        tid = request.form.get("teacherId")
        name = request.form.get("teacherName")
        if tid and name:
            session["teacher"] = {"id": tid, "name": name}
            return redirect(url_for("teacher.dashboard"))
        flash("Please provide Teacher ID & Name", "warning")
    return render_template("teacher_login.html")

@bp.route("/dashboard")
def dashboard():
    if "teacher" not in session:
        flash("Please log in", "warning")
        return redirect(url_for("teacher.login"))
    # load current working marks if any (sessional marks)
    marks = _load("sessional_marks.json", default={}).get("records", [])
    return render_template("teacher_dashboard.html", marks=marks, teacher=session.get("teacher"))

@bp.route("/upload-csv", methods=["POST"])
def upload_csv():
    """
    Accepts a multipart CSV upload, parses and returns parsed rows for preview.
    """
    f = request.files.get("file")
    if not f:
        return jsonify({"error":"no file"}), 400
    text = f.stream.read().decode("utf-8", errors="replace")
    rows = []
    for line in csv.reader(io.StringIO(text)):
        if not any(cell.strip() for cell in line):
            continue
        rows.append(line)
    return jsonify({"ok": True, "rows": rows})

@bp.route("/save-marks", methods=["POST"])
def save_marks():
    """
    Accepts JSON payload like { marks: [ ... ], meta: {...} } and stores server-side
    """
    data = request.get_json() or {}
    marks = data.get("marks") or []
    meta = data.get("meta") or {"lastSavedAt": datetime.utcnow().isoformat(), "lastSavedBy": session.get("teacher", {})}
    to_store = {"_meta": meta, "records": marks}
    _save("sessional_marks.json", to_store)
    return jsonify({"ok": True, "saved_at": meta["lastSavedAt"]})
