import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


KEY = "qizai-dashboard"


def default_data():
    return {
        "account": "奇仔旅行内容工作台",
        "sourceUrl": "",
        "updatedAt": "",
        "status": "manual",
        "message": "还没有导入旅行笔记数据。点击右上角导入 CSV 或 JSON。",
        "daily": [],
        "notes": [],
    }


def redis_config():
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return url, token


def redis_command(command):
    url, token = redis_config()
    if not url or not token:
        raise RuntimeError("Database is not configured")

    request = Request(
        url.rstrip("/"),
        data=json.dumps(command).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload and payload["error"]:
        raise RuntimeError(payload["error"])
    return payload.get("result")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            stored = redis_command(["GET", KEY])
            payload = json.loads(stored) if stored else default_data()
            self.send_json(200, payload)
        except (RuntimeError, HTTPError, URLError, TimeoutError) as error:
            self.send_json(503, {"ok": False, "error": str(error)})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload.get("daily"), list) or not isinstance(payload.get("notes"), list):
                self.send_json(400, {"ok": False, "error": "Payload must include daily and notes arrays"})
                return
            redis_command(["SET", KEY, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))])
            self.send_json(200, {"ok": True})
        except json.JSONDecodeError:
            self.send_json(400, {"ok": False, "error": "Invalid JSON"})
        except (RuntimeError, HTTPError, URLError, TimeoutError) as error:
            self.send_json(503, {"ok": False, "error": str(error)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
