# routes/student_routes.py
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from pathlib import Path
import os, json, io, csv
from datetime import datetime

bp = Blueprint("student", __name__, url_prefix="")

DATA_DIR = os.path.join(Path(__file__).resolve().parents[1], "data")

def _load(fname, default=None):
    p = os.path.join(DATA_DIR, fname)
    if not os.path.exists(p):
        return default
    try:
        with open(p,"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

@bp.route("/results")
def results_page():
    # Renders results.html which uses localStorage or can call API for server-side data
    return render_template("results.html")

@bp.route("/student/lookup", methods=["GET"])
def lookup_student():
    """
    Query param: roll or student_id
    Returns JSON student data if present in semester_results.json
    """
    q = request.args.get("q")
    data = _load("semester_results.json", default=None)
    if not data:
        return jsonify({"ok": False, "message": "No results on server"}), 404
    # accept wrapper { _meta, records }
    records = data.get("records") if isinstance(data, dict) and data.get("records") else data if isinstance(data, list) else []
    for r in records:
        if str(r.get("roll_no")) == str(q) or str(r.get("student_id")) == str(q):
            return jsonify({"ok": True, "student": r})
    return jsonify({"ok": False, "message": "not found"}), 404

@bp.route("/student/download/<roll_no>.csv")
def download_student_csv(roll_no):
    data = _load("semester_results.json", default=None)
    if not data:
        return "No results stored", 404
    records = data.get("records") if isinstance(data, dict) else data
    student = next((r for r in records if str(r.get("roll_no"))==str(roll_no) or str(r.get("student_id"))==str(roll_no)), None)
    if not student:
        return "No student", 404
    # build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["roll_no","student_id","name","class","semester","year","marks","gpa"])
    sems = student.get("semesters", [])
    for s in sems:
        writer.writerow([student.get("roll_no"), student.get("student_id"), student.get("name"), student.get("class"),
                         s.get("sem"), s.get("year"), s.get("marks"), s.get("gpa")])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name=f"results_{roll_no}.csv")
