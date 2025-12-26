# routes/face_routes.py
from flask import Blueprint, request, jsonify, current_app, send_file
from pathlib import Path
import os, base64, io
from datetime import datetime

bp = Blueprint("face", __name__, url_prefix="/face")

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOADS = os.path.join(BASE_DIR, "static", "uploads")
TEACHER_FACES = os.path.join(UPLOADS, "teacher_faces")
STUDENT_FACES = os.path.join(UPLOADS, "student_faces")

os.makedirs(TEACHER_FACES, exist_ok=True)
os.makedirs(STUDENT_FACES, exist_ok=True)

def _save_dataurl(dataurl, dest_path):
    header, encoded = dataurl.split(",",1)
    data = base64.b64decode(encoded)
    with open(dest_path, "wb") as f:
        f.write(data)
    return dest_path

@bp.route("/enroll/teacher", methods=["POST"])
def enroll_teacher():
    # Accepts form fields teacher_id,name and photo (file or dataurl)
    teacher_id = request.form.get("teacher_id") or request.form.get("id")
    photo_data = request.form.get("photo_base64")
    if "file" in request.files and request.files["file"]:
        f = request.files["file"]
        fname = f"{teacher_id}_{int(datetime.utcnow().timestamp())}_{f.filename}"
        dest = os.path.join(TEACHER_FACES, fname)
        f.save(dest)
        return jsonify({"ok": True, "path": dest})
    if photo_data and photo_data.startswith("data:"):
        ext = "jpg"
        fname = f"{teacher_id}_{int(datetime.utcnow().timestamp())}.{ext}"
        dest = os.path.join(TEACHER_FACES, fname)
        _save_dataurl(photo_data, dest)
        return jsonify({"ok": True, "path": dest})
    return jsonify({"ok": False, "message":"no image"}), 400

@bp.route("/enroll/student", methods=["POST"])
def enroll_student():
    # similar to enroll_teacher
    student_id = request.form.get("student_id") or request.form.get("id")
    photo_data = request.form.get("photo_base64_student") or request.form.get("photo_base64")
    if "file" in request.files and request.files["file"]:
        f = request.files["file"]
        fname = f"{student_id}_{int(datetime.utcnow().timestamp())}_{f.filename}"
        dest = os.path.join(STUDENT_FACES, fname)
        f.save(dest)
        return jsonify({"ok": True, "path": dest})
    if photo_data and photo_data.startswith("data:"):
        ext = "jpg"
        fname = f"{student_id}_{int(datetime.utcnow().timestamp())}.{ext}"
        dest = os.path.join(STUDENT_FACES, fname)
        _save_dataurl(photo_data, dest)
        return jsonify({"ok": True, "path": dest})
    return jsonify({"ok": False, "message":"no image"}), 400

@bp.route("/recognize", methods=["POST"])
def recognize():
    """
    Replace this stub with your real recognizer.
    Accepts JSON: { image: dataURL } or multipart file.
    Returns { ok: True, id, name } on match.
    """
    payload = {}
    if request.is_json:
        payload = request.get_json()
    image = payload.get("image") if payload else None
    if not image and "file" in request.files:
        f = request.files["file"]
        tmp = os.path.join(UPLOADS, f"capture_{int(datetime.utcnow().timestamp())}_{f.filename}")
        f.save(tmp)
        image = None
        # you can process tmp
    # stub response
    return jsonify({"ok": False, "message":"recognition not implemented"})
