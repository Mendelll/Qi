#!/usr/bin/env python3
import argparse
import hashlib
import hmac
from http import cookies
import json
import mimetypes
import secrets
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "dashboard.sqlite"
SEED_PATH = ROOT / "data" / "xiaohongshu-dashboard.json"
SESSION_COOKIE = "qizai_dashboard_session"


def default_data():
    return {
        "account": "小红书主页",
        "sourceUrl": "",
        "updatedAt": "",
        "status": "manual",
        "message": "还没有导入数据。点击右上角导入 CSV 或 JSON。",
        "daily": [],
        "notes": [],
    }


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            payload TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return db


def read_payload():
    with connect_db() as db:
        row = db.execute("SELECT payload FROM dashboard_state WHERE id = 1").fetchone()
    if row:
        return json.loads(row[0])
    if SEED_PATH.exists():
        try:
            return json.loads(SEED_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default_data()


def write_payload(payload):
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with connect_db() as db:
        db.execute(
            """
            INSERT INTO dashboard_state (id, payload, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (serialized,),
        )


class DashboardHandler(SimpleHTTPRequestHandler):
    password = ""
    session_token = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/login":
            self.send_login()
            return
        if not self.is_authorized():
            self.redirect_to_login()
            return
        if self.path.split("?", 1)[0] == "/api/dashboard":
            self.send_json(200, read_payload())
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route == "/login":
            self.handle_login()
            return
        if not self.is_authorized():
            self.send_json(401, {"ok": False, "error": "Unauthorized"})
            return
        if route != "/api/dashboard":
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json(400, {"ok": False, "error": "Invalid JSON"})
            return
        if not isinstance(payload.get("daily"), list) or not isinstance(payload.get("notes"), list):
            self.send_json(400, {"ok": False, "error": "Payload must include daily and notes arrays"})
            return
        write_payload(payload)
        self.send_json(200, {"ok": True})

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def is_authorized(self):
        if not self.password:
            return True
        header = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie()
        jar.load(header)
        morsel = jar.get(SESSION_COOKIE)
        return bool(morsel and hmac.compare_digest(morsel.value, self.session_token))

    def redirect_to_login(self):
        self.send_response(302)
        self.send_header("Location", "/login")
        self.end_headers()

    def send_login(self, error=""):
        error_html = f"<p class='error'>{error}</p>" if error else ""
        body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>登录 · 奇仔的数据面板</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #f6f4ef;
      color: #1f2428;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    form {{
      width: min(380px, calc(100vw - 36px));
      padding: 24px;
      background: #fffdf8;
      border: 1px solid #e7e0d4;
      border-radius: 8px;
      box-shadow: 0 12px 32px rgba(33, 29, 23, .08);
    }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    p {{ margin: 0 0 18px; color: #6b7280; font-size: 14px; }}
    label {{ display: grid; gap: 8px; color: #6b7280; font-size: 13px; }}
    input {{
      width: 100%;
      height: 42px;
      border: 1px solid #e7e0d4;
      border-radius: 8px;
      padding: 0 12px;
      font: inherit;
    }}
    button {{
      width: 100%;
      height: 42px;
      margin-top: 14px;
      border: 0;
      border-radius: 8px;
      background: #e84855;
      color: white;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
    }}
    .error {{ color: #bd2635; }}
  </style>
</head>
<body>
  <form method="post" action="/login">
    <h1>奇仔的数据面板</h1>
    <p>输入访问密码后继续。</p>
    {error_html}
    <label>
      访问密码
      <input name="password" type="password" autocomplete="current-password" autofocus>
    </label>
    <button type="submit">进入面板</button>
  </form>
</body>
</html>""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_login(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        submitted = parse_qs(raw_body).get("password", [""])[0]
        if hmac.compare_digest(submitted, self.password):
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={self.session_token}; Path=/; HttpOnly; SameSite=Lax")
            self.end_headers()
        else:
            self.send_login("密码不正确")

    def guess_type(self, path):
        if path.endswith(".js"):
            return "text/javascript"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def main():
    parser = argparse.ArgumentParser(description="Serve Qizai dashboard with a SQLite database.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4174, type=int)
    parser.add_argument("--password", default="", help="Require a password before showing the dashboard.")
    args = parser.parse_args()
    with connect_db():
        pass
    DashboardHandler.password = args.password
    DashboardHandler.session_token = hashlib.sha256(f"{args.password}:{secrets.token_hex(16)}".encode("utf-8")).hexdigest()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving 奇仔的数据面板 on http://{args.host}:{args.port}/")
    print(f"SQLite database: {DB_PATH}")
    if args.password:
        print("Password protection: enabled")
    server.serve_forever()


if __name__ == "__main__":
    main()
