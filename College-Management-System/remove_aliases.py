# remove_aliases.py
import re
from pathlib import Path
p = Path("app.py")
if not p.exists():
    print("No app.py found in current directory:", p.resolve())
    raise SystemExit(1)

bak = p.with_suffix(".py.bak")
bak.write_bytes(p.read_bytes())
print("Backup written to", bak)

text = p.read_text(encoding="utf-8")

# Remove decorators + alias function blocks that look like:
# @app.route('/admin/login' ... )
# def admin_login_alias(...):
#    ...
pattern = re.compile(
    r"(?:\n\s*@app\.route\([^\n]*\)\s*\n\s*def\s+(?:admin_login_alias|login_alias|teacher_login_alias)\s*\([^)]*\):\s*(?:\n(?:\s+.*?))*?)",
    flags=re.IGNORECASE
)

new_text, n = pattern.subn("\n", text)
print(f"Removed {n} alias blocks (decorator + function).")

# Also remove any standalone def admin_login_alias left without decorator
pattern2 = re.compile(r"\n\s*def\s+(?:admin_login_alias|login_alias|teacher_login_alias)\s*\([^)]*\):\s*(?:\n(?:\s+.*?))*", flags=re.IGNORECASE)
new_text2, n2 = pattern2.subn("\n", new_text)
print(f"Removed {n2} standalone alias defs.")

# Safety check: ensure admin blueprint import still exists
if "routes.admin_routes" not in new_text2 and "admin_routes" not in new_text2:
    print("Warning: app.py no longer imports admin_routes. Please check that you are editing the correct app.py.")
else:
    p.write_text(new_text2, encoding="utf-8")
    print("Written cleaned app.py. Restart the Flask server now.")
