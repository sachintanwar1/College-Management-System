# app.py
import os
import io
import json
import base64
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    send_file, abort, flash
)
from werkzeug.utils import secure_filename

# -------------- Configuration --------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")
TEACHER_FACES = os.path.join(UPLOADS_DIR, "teacher_faces")
STUDENT_FACES = os.path.join(UPLOADS_DIR, "student_faces")
SESSIONAL_MARKS_FILE = os.path.join(DATA_DIR, "sessional_marks.json")
SEMESTER_RESULTS_FILE = os.path.join(DATA_DIR, "semester_results.json")

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg"}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(TEACHER_FACES, exist_ok=True)
os.makedirs(STUDENT_FACES, exist_ok=True)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")

# --- Register blueprints (routes) ---
def try_register(import_path):
    try:
        module = __import__(import_path, fromlist=['bp'])
        bp = getattr(module, 'bp', None)
        if bp is None:
            print(f"Warning: module {import_path} has no 'bp' attribute")
            return
        app.register_blueprint(bp)
        print(f"Registered blueprint from {import_path}")
    except Exception as e:
        print(f"Warning: could not register blueprint {import_path}: {e}")

try_register('routes.admin_routes')
try_register('routes.teacher_routes')
try_register('routes.student_routes')
try_register('routes.face_routes')
try_register('routes.api_routes')

# --- Initialize SQLAlchemy models and create tables if needed ---
try:
    from database.models import db, create_all_if_needed
    # configure SQLAlchemy DB location (fallback to sqlite in instance/)
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///instance/database.sqlite3"
    )

    # Initialize db once
    db.init_app(app)

    # Create tables (use db.create_all() instead of create_all_if_needed(app)
    # to avoid calling db.init_app() twice inside the helper).
    with app.app_context():
        db.create_all()
except Exception as _err:
    # If database package is not available yet, print a warning and continue.
    print("Warning: could not initialize SQLAlchemy models:", _err)






# -------------- Helper functions --------------
def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXT

def save_base64_image(data_url, dest_path):
    """
    data_url: "data:image/jpeg;base64,...."
    dest_path: file path to save (including extension)
    """
    header, encoded = data_url.split(",", 1)
    # optionally inspect header for mimetype
    data = base64.b64decode(encoded)
    with open(dest_path, "wb") as f:
        f.write(data)
    return dest_path

def make_unique_filename(prefix, orig_filename):
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    safe = secure_filename(orig_filename)
    return f"{prefix}_{ts}_{safe}"

# -------------- Routes: pages --------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/teacher-login")
def teacher_login_page():
    return render_template("teacher_login.html")

@app.route("/teacher-dashboard")
def teacher_dashboard_page():
    return render_template("teacher_dashboard.html")

@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")

@app.route("/results")
def results_page():
    return render_template("results.html")
@app.route("/camera")
def camera_page():
    return render_template("camera.html")



@app.route('/_list_routes')
def _list_routes():
    return '<br>'.join(sorted(f"{r.endpoint} -> {r.rule}" for r in app.url_map.iter_rules()))



# Generic error handler page if template exists
@app.route("/error")
def error_page():
    return render_template("error.html"), 500

# -------------- API: Upload / registration --------------
@app.route("/register-teacher", methods=["POST"])
def register_teacher():
    """
    Accepts either:
    - multipart form: fields (teacher_name, teacher_id, department, assigned_classes) + photo_file
    - OR photo_base64 (dataURL) in a text field
    Saves profile JSON in data/teachers.json and the face image in static/uploads/teacher_faces/.
    """
    name = request.form.get("teacher_name") or request.form.get("name")
    teacher_id = request.form.get("teacher_id")
    department = request.form.get("department", "")
    assigned_classes = request.form.get("assigned_classes", "")

    if not name or not teacher_id:
        return "Missing name or teacher_id", 400

    # load existing teachers
    teachers = load_json(os.path.join(DATA_DIR, "teachers.json"), default=[])
    # store profile
    profile = {
        "name": name,
        "teacher_id": teacher_id,
        "department": department,
        "assigned_classes": assigned_classes,
        "enrolled_at": datetime.utcnow().isoformat()
    }

    # Handle image (file or base64)
    saved_image_path = None
    if "photo_file" in request.files and request.files["photo_file"]:
        f = request.files["photo_file"]
        if f and allowed_file(f.filename):
            fname = make_unique_filename(teacher_id, f.filename)
            dest = os.path.join(TEACHER_FACES, fname)
            f.save(dest)
            saved_image_path = os.path.relpath(dest, BASE_DIR)
    else:
        # base64 field
        base64_field = request.form.get("photo_base64")
        if base64_field and base64_field.startswith("data:"):
            # choose extension from header
            header = base64_field.split(",", 1)[0]
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "png" in header:
                ext = "png"
            else:
                ext = "jpg"
            fname = make_unique_filename(teacher_id, f"face.{ext}")
            dest = os.path.join(TEACHER_FACES, fname)
            try:
                save_base64_image(base64_field, dest)
                saved_image_path = os.path.relpath(dest, BASE_DIR)
            except Exception as ex:
                print("Error saving base64 image:", ex)

    profile["face_image"] = saved_image_path
    teachers.append(profile)
    save_json(os.path.join(DATA_DIR, "teachers.json"), teachers)

    # redirect back to dashboard or return JSON
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"ok": True, "profile": profile})
    flash("Teacher enrolled successfully", "success")
    return redirect(url_for("dashboard"))


@app.route("/register-student", methods=["POST"])
def register_student():
    """
    Similar to register_teacher. Saves student profile and face image.
    """
    name = request.form.get("student_name") or request.form.get("name")
    student_id = request.form.get("student_id")
    class_section = request.form.get("class_section", "")
    roll_no = request.form.get("roll_no", "")

    if not name or not student_id:
        return "Missing name or student_id", 400

    students = load_json(os.path.join(DATA_DIR, "students.json"), default=[])
    profile = {
        "name": name,
        "student_id": student_id,
        "class": class_section,
        "roll_no": roll_no,
        "enrolled_at": datetime.utcnow().isoformat()
    }

    saved_image_path = None
    if "photo_file_student" in request.files and request.files["photo_file_student"]:
        f = request.files["photo_file_student"]
        if f and allowed_file(f.filename):
            fname = make_unique_filename(student_id, f.filename)
            dest = os.path.join(STUDENT_FACES, fname)
            f.save(dest)
            saved_image_path = os.path.relpath(dest, BASE_DIR)
    else:
        base64_field = request.form.get("photo_base64_student")
        if base64_field and base64_field.startswith("data:"):
            header = base64_field.split(",", 1)[0]
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "png" in header:
                ext = "png"
            else:
                ext = "jpg"
            fname = make_unique_filename(student_id, f"face.{ext}")
            dest = os.path.join(STUDENT_FACES, fname)
            try:
                save_base64_image(base64_field, dest)
                saved_image_path = os.path.relpath(dest, BASE_DIR)
            except Exception as ex:
                print("Error saving base64 image:", ex)

    profile["face_image"] = saved_image_path
    students.append(profile)
    save_json(os.path.join(DATA_DIR, "students.json"), students)

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"ok": True, "profile": profile})
    flash("Student enrolled successfully", "success")
    return redirect(url_for("dashboard"))

# -------------- API: Marks & Results --------------
@app.route("/api/upload-marks", methods=["POST"])
def api_upload_marks():
    """
    Accepts JSON payload:
      {
        "marks": [ { student_id, name, class, roll_no, semester, marks, gpa }, ... ],
        "lastSavedBy": { id, name },
        "lastSavedAt": ISOString
      }
    Saves to data/sessional_marks.json (server-side).
    """
    if not request.is_json:
        return jsonify({"error": "Only JSON accepted"}), 400
    payload = request.get_json()
    # minimal validation
    marks = payload.get("marks") or payload.get("records") or []
    meta = payload.get("meta") or {"lastSavedAt": datetime.utcnow().isoformat(), "lastSavedBy": payload.get("lastSavedBy", {})}
    stored = {"_meta": meta, "records": marks}
    save_json(SESSIONAL_MARKS_FILE, stored)
    return jsonify({"ok": True, "saved_at": meta.get("lastSavedAt")})

@app.route("/api/get-marks", methods=["GET"])
def api_get_marks():
    """
    Returns the stored marks object (for teacher pages or client-side).
    """
    saved = load_json(SESSIONAL_MARKS_FILE, default={})
    return jsonify(saved)

@app.route("/api/get-semester-results", methods=["GET"])
def api_get_semester_results():
    """
    Returns semester results (students array) -> used by results page
    """
    raw = load_json(SEMESTER_RESULTS_FILE, default=None)
    if raw is None:
        # try fallback to sessional marks to convert into student centric structure (very simple)
        return jsonify({"ok": False, "message": "No semester_results found on server"})
    return jsonify({"ok": True, "data": raw})

@app.route("/api/publish-semester-results", methods=["POST"])
def api_publish_semester_results():
    """
    Endpoint to upload full semester_results JSON (array of students with semesters array).
    Example payload: [ { roll_no, student_id, name, class, semesters: [ ... ] }, ... ]
    """
    if not request.is_json:
        return jsonify({"error": "Only JSON accepted"}), 400
    payload = request.get_json()
    # minimal check: payload must be list
    if not isinstance(payload, list):
        return jsonify({"error": "Expecting top-level array of student objects"}), 400
    # optionally add meta wrapper
    meta = {"lastSavedAt": datetime.utcnow().isoformat(), "lastSavedBy": {"id": "api", "name": "API"}}
    to_store = {"_meta": meta, "records": payload}
    save_json(SEMESTER_RESULTS_FILE, to_store)
    return jsonify({"ok": True, "count": len(payload), "saved_at": meta["lastSavedAt"]})

# -------------- Face recognition stub --------------
# persistence for attendance captures
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")
CAPTURE_DIR = os.path.join(UPLOADS_DIR, "captures")
os.makedirs(CAPTURE_DIR, exist_ok=True)

@app.route("/face/recognize", methods=["POST"])
def face_recognize():
    """
    Demo capture+persist endpoint:
    - Accepts JSON { image: dataURL } OR form-file named "file"
    - Saves image to static/uploads/captures/
    - Appends an attendance record to data/attendance.json
    - Returns { ok: True, id, name, status, ts } on success
    Replace recognition logic with your real model later.
    """
    image_data = None
    filename = None

    # 1) Get image payload
    if request.is_json:
        image_data = request.get_json().get("image")
    elif "image" in request.form:
        image_data = request.form.get("image")
    elif "file" in request.files:
        f = request.files["file"]
        filename = make_unique_filename("capture", f.filename or "capture.jpg")
        dest = os.path.join(CAPTURE_DIR, filename)
        f.save(dest)

    # 2) If dataURL provided, save it to file
    if image_data and isinstance(image_data, str) and image_data.startswith("data:"):
        try:
            header = image_data.split(",", 1)[0]
            ext = "jpg"
            if "png" in header: ext = "png"
            filename = make_unique_filename("capture", f"capture.{ext}")
            dest = os.path.join(CAPTURE_DIR, filename)
            _, b64 = image_data.split(",", 1)
            with open(dest, "wb") as fh:
                fh.write(base64.b64decode(b64))
        except Exception as e:
            print("Failed to save capture:", e)
            return jsonify({"ok": False, "message": "Failed to save image"}), 500

    # 3) Demo recognition / record creation
    if filename:
        ts = datetime.utcnow().isoformat()
        demo_id = f"DEMO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        demo_name = "Demo Student"
        status = "present"
        record = {
            "id": demo_id,
            "name": demo_name,
            "status": status,
            "ts": ts,
            "image": os.path.relpath(os.path.join(CAPTURE_DIR, filename), BASE_DIR)
        }

        arr = load_json(ATTENDANCE_FILE, default=[])
        arr.append(record)
        save_json(ATTENDANCE_FILE, arr)

        return jsonify({"ok": True, "id": record["id"], "name": record["name"], "status": record["status"], "ts": record["ts"]})

    return jsonify({"ok": False, "message": "No image provided"}), 400


# Optional helper endpoints — add right after face_recognize for convenience:
@app.route("/api/get-attendance", methods=["GET"])
def api_get_attendance():
    return jsonify(load_json(ATTENDANCE_FILE, default=[]))

@app.route("/api/clear-attendance", methods=["POST"])
def api_clear_attendance():
    save_json(ATTENDANCE_FILE, [])
    return jsonify({"ok": True})


# -------------- Report generation --------------
@app.route("/report/<roll_no>", methods=["GET"])
def generate_report(roll_no):
    """
    Renders report_template.html for a given roll_no.
    If query param ?pdf=1 is present and pdfkit is installed + wkhtmltopdf available, returns PDF.
    """
    # load semester results wrapper
    raw = load_json(SEMESTER_RESULTS_FILE, default=None)
    records = []
    meta = {}
    if raw is None:
        return "No semester results available on server. Upload via /api/publish-semester-results or use admin upload.", 404
    if isinstance(raw, dict) and raw.get("records"):
        records = raw["records"]
        meta = raw.get("_meta", {})
    elif isinstance(raw, list):
        records = raw
    else:
        return "Unexpected data format in semester results file", 500

    # find the student
    student = None
    for r in records:
        # match by roll_no (string)
        if str(r.get("roll_no")) == str(roll_no) or str(r.get("student_id")) == str(roll_no):
            student = r
            break
    if not student:
        return f"No results found for roll no {roll_no}", 404

    total_marks = 0
    gpa_sum = 0
    gpa_count = 0
    for s in student.get("semesters", []):
        if isinstance(s.get("marks"), (int, float)):
            total_marks += s["marks"]
        if isinstance(s.get("gpa"), (int, float)):
            gpa_sum += s["gpa"]; gpa_count += 1
    avg_gpa = round(gpa_sum / gpa_count, 2) if gpa_count else None

    context = {
        "student": student,
        "generated_at": datetime.utcnow().isoformat(),
        "prepared_by": meta.get("lastSavedBy", {"name": "System"}).get("name", "System"),
        "total_marks": total_marks if total_marks else "-",
        "avg_gpa": avg_gpa if avg_gpa is not None else "-",
        "remarks": meta.get("remarks", "")
    }

    # if pdf requested, try pdfkit
    want_pdf = request.args.get("pdf") == "1"
    if want_pdf:
        try:
            import pdfkit
            rendered = render_template("report_template.html", **context)
            # you may need to adjust wkhtmltopdf path via configuration
            pdf = pdfkit.from_string(rendered, False)
            return send_file(io.BytesIO(pdf), mimetype="application/pdf",
                             as_attachment=True, download_name=f"report_{roll_no}.pdf")
        except Exception as e:
            # fallback to HTML if PDF generation failed
            print("PDF generation failed:", e)
            return render_template("report_template.html", **context)
    return render_template("report_template.html", **context)

# -------------- Simple downloads / admin helpers --------------
@app.route("/download/sessional_marks")
def download_sessional_marks():
    obj = load_json(SESSIONAL_MARKS_FILE, default=None)
    if not obj:
        return "No sessional marks stored", 404
    return jsonify(obj)

# -------------- Static helpers for dev --------------
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html"), 500

# -------------- Run --------------
if __name__ == "__main__":
    # Debug server for development
    app.run(host="0.0.0.0", port=5000, debug=True)
