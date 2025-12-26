# routes/api_routes.py
from flask import Blueprint, request, jsonify
from pathlib import Path
import os, json
from datetime import datetime

bp = Blueprint("api", __name__, url_prefix="/api")
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

def _save(fname, obj):
    p = os.path.join(DATA_DIR, fname)
    with open(p,"w",encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

@bp.route("/get-marks")
def get_marks():
    return jsonify(_load("sessional_marks.json", default={}))
