#!/usr/bin/env python3
"""
run.py - launcher for the Advanced Face Attendance System Flask app.

Usage:
  # Development (default)
  python run.py

  # Specify host/port
  python run.py --host 0.0.0.0 --port 5000

  # Use waitress WSGI server (recommended for simple production)
  python run.py --waitress

Environment:
  - FLASK_ENV=production   => uses ProductionConfig from config.py
  - FLASK_ENV=development  => uses DevelopmentConfig (default)
  - FLASK_SECRET_KEY       => override secret key
"""
import os
import argparse
import logging
from pathlib import Path

# import app and config classes
try:
    from app import app  # app.py should define `app`
except Exception as e:
    raise RuntimeError("Unable to import Flask app from app.py — ensure app.py exists and defines `app`.") from e

try:
    from config import DevelopmentConfig, ProductionConfig, BaseConfig
except Exception:
    # fallback: safe defaults if config.py missing
    DevelopmentConfig = ProductionConfig = BaseConfig = None

def ensure_dirs():
    """
    Ensure directories declared in config exist (data, uploads, face dirs).
    """
    cfg = app.config
    paths = []
    # try reading common keys (safe-guarded)
    for key in ("DATA_DIR", "UPLOADS_DIR", "TEACHER_FACE_DIR", "STUDENT_FACE_DIR"):
        p = cfg.get(key) or (BaseConfig.__dict__.get(key) if BaseConfig else None)
        if p:
            paths.append(Path(p))
    # also ensure instance folder for SQLite
    inst = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"))
    paths.append(inst)
    for p in paths:
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            # ignore permission errors here; will surface later if needed
            pass

def configure_app_from_env():
    """Load config object into app depending on FLASK_ENV and environment overrides."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    if DevelopmentConfig is None:
        # nothing to do
        return
    if env == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Optional overrides from environment variables
    secret = os.environ.get("FLASK_SECRET_KEY")
    if secret:
        app.config["SECRET_KEY"] = secret

    # configure pdfkit if requested and available
    if app.config.get("ENABLE_PDF_EXPORT") and app.config.get("WKHTMLTOPDF_PATH"):
        try:
            import pdfkit
            cfg = pdfkit.configuration(wkhtmltopdf=app.config["WKHTMLTOPDF_PATH"])
            app.config["PDFKIT_CONFIG"] = cfg
            logging.getLogger(__name__).info("pdfkit configured with wkhtmltopdf: %s", app.config["WKHTMLTOPDF_PATH"])
        except Exception as e:
            logging.getLogger(__name__).warning("pdfkit/wkhtmltopdf not available or failed to configure: %s", e)

def parse_args():
    p = argparse.ArgumentParser(description="Run the Face Attendance Flask app")
    p.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Host to bind (default 127.0.0.1)")
    p.add_argument("--port", default=int(os.environ.get("PORT", 5000)), type=int, help="Port to bind (default 5000)")
    p.add_argument("--waitress", action="store_true", help="Run using waitress (production WSGI) if installed")
    p.add_argument("--debug", action="store_true", help="Enable Flask debug mode (overrides config)")
    return p.parse_args()

def main():
    args = parse_args()

    # configure app & dirs
    configure_app_from_env()
    ensure_dirs()

    # set logging level
    logging.basicConfig(level=logging.DEBUG if app.config.get("DEBUG", False) else logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.DEBUG if app.config.get("DEBUG", False) else logging.INFO)

    host = args.host
    port = args.port

    if args.debug:
        app.config["DEBUG"] = True
        logging.getLogger(__name__).info("Debug mode enabled via CLI flag")

    # Run using waitress if requested and available
    if args.waitress:
        try:
            from waitress import serve
            logging.getLogger(__name__).info("Starting app with waitress on %s:%d", host, port)
            serve(app, host=host, port=port)
            return
        except Exception as e:
            logging.getLogger(__name__).warning("waitress not available or failed to start (%s). Falling back to Flask dev server.", e)

    # Default: Flask dev server (suitable for development only)
    logging.getLogger(__name__).info("Starting Flask development server on %s:%d (debug=%s)", host, port, app.config.get("DEBUG", False))
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False), use_reloader=app.config.get("DEBUG", False))

if __name__ == "__main__":
    main()
