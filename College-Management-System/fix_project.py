# fix_project.py
import re, os, shutil, sys
from pathlib import Path

root = Path.cwd()
print("Working in", root)

# backup entire project folder just in case
bak = root.parent / (root.name + "_bak_for_fix")
if not bak.exists():
    print("Creating backup at", bak)
    shutil.copytree(root, bak)
else:
    print("Backup already present at", bak)

# 1) index.html replacement
idx = root / "templates" / "index.html"
if idx.exists():
    text = idx.read_text(encoding="utf-8")
    new = re.sub(r"url_for\(\s*['\"]login['\"]\s*\)", "url_for('admin.admin_login')", text)
    if new != text:
        idx.write_text(new, encoding="utf-8")
        print("Patched templates/index.html")
else:
    print("templates/index.html not found")

# 2) login.html form action
login = root / "templates" / "login.html"
if login.exists():
    text = login.read_text(encoding="utf-8")
    # set action to admin.admin_login and method POST
    text = re.sub(r"<form([^>]*)action\s*=\s*\"[^\"]*\"([^>]*)>", r"<form\1action=\"{{ url_for('admin.admin_login') }}\"\2>", text, count=1)
    text = re.sub(r"<form([^>]*)method\s*=\s*\"[^\"]*\"([^>]*)>", r"<form\1method=\"POST\"\2>", text, count=1)
    login.write_text(text, encoding="utf-8")
    print("Patched templates/login.html")
else:
    print("templates/login.html not found")

# 3) app.py fixes: remove alias defs and replace blueprint registration
app_path = root / "app.py"
if app_path.exists():
    text = app_path.read_text(encoding="utf-8")
    orig = text

    # remove @app.route(.../admin/login ...) ... def ..._alias blocks
    text = re.sub(r"\n\s*@app\.route\([^)]*['\"]/(?:admin/login|login|teacher/login)['\"][^\)]*\)\s*\n\s*def\s+\w+_alias\s*\([^)]*\):\s*(?:\n(?:\s+.*?))*", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\n\s*def\s+\w+_alias\s*\([^)]*\):\s*(?:\n(?:\s+.*?))*", "\n", text, flags=re.IGNORECASE)
    # replace the blueprint registration try-except with try_register if present
    old_block = re.compile(r"(?s)# --- Register blueprints \(routes\) ---.*?except Exception as _err:\s*print\([^\)]*\)\s*", flags=re.MULTILINE)
    if old_block.search(text):
        text = old_block.sub(
            "\n# --- Register blueprints (routes) ---\n"
            "def try_register(import_path):\n"
            "    try:\n"
            "        module = __import__(import_path, fromlist=['bp'])\n"
            "        bp = getattr(module, 'bp', None)\n"
            "        if bp is None:\n"
            "            print(f\"Warning: module {import_path} has no 'bp' attribute\")\n"
            "            return\n"
            "        app.register_blueprint(bp)\n"
            "        print(f\"Registered blueprint from {import_path}\")\n"
            "    except Exception as e:\n"
            "        print(f\"Warning: could not register blueprint {import_path}: {e}\")\n\n"
            "try_register('routes.admin_routes')\n"
            "try_register('routes.teacher_routes')\n"
            "try_register('routes.student_routes')\n"
            "try_register('routes.face_routes')\n"
            "try_register('routes.api_routes')\n\n",
            text
        )
        print("Replaced blueprint registration block in app.py")
    else:
        print("No blueprint registration block pattern found; leaving app.py imports as-is")

    if text != orig:
        app_path.write_text(text, encoding="utf-8")
        print("Patched app.py (aliases removed / registration updated)")
    else:
        print("No changes made to app.py")
else:
    print("app.py not found in current folder")

# 4) Ensure instance/db and data/.keep
inst = root / "instance"
if not inst.exists():
    inst.mkdir(parents=True, exist_ok=True)
    print("Created instance/")

dbfile = inst / "database.sqlite3"
if not dbfile.exists():
    dbfile.write_bytes(b"")
    print("Created instance/database.sqlite3")

data_dir = root / "data"
if not data_dir.exists():
    data_dir.mkdir(parents=True, exist_ok=True)
    print("Created data/")

keep = data_dir / ".keep"
if not keep.exists():
    keep.write_bytes(b"")
    print("Created data/.keep")

print("All done. Restart your Flask app with: python app.py")
