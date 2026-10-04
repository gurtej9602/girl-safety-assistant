import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_INSTRUCTION = """You are a helpful, friendly AI assistant inside a chat application.
Answer the user's questions clearly and naturally. Be concise when a short answer is enough.
If the user asks for safety-related advice, prioritize practical, non-dangerous steps and encourage
contacting trusted people or appropriate emergency services when there is immediate danger.
Do not claim to be a human, doctor, lawyer, police officer, or emergency service.
Do not invent phone numbers, laws, addresses, or real-world resources.
"""

def process_chat(data):
    api_key = os.environ.get("GEMINI_API_KEY", API_KEY)
    model = os.environ.get("GEMINI_MODEL", MODEL)

    if not api_key:
        return {"error": "GEMINI_API_KEY is not configured in Vercel environment variables."}, 500

    message = str(data.get("message", "")).strip()
    history = data.get("history", [])
    if not message:
        return {"error": "Please enter a message."}, 400
    if len(message) > 8000:
        return {"error": "Message is too long. Keep it under 8000 characters."}, 400
    if not isinstance(history, list):
        history = []

    contents = []
    for item in history[-20:]:
        role = "model" if item.get("role") == "model" else "user"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    if not contents or contents[-1]["role"] != "user" or contents[-1]["parts"][0]["text"] != message:
        contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urlopen(req, timeout=55) as r:
        result = json.loads(r.read().decode("utf-8"))

    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no response.")
    parts = candidates[0].get("content", {}).get("parts", [])
    reply = "".join(p.get("text", "") for p in parts if p.get("text")).strip()
    if not reply:
        raise RuntimeError("Gemini returned an empty response.")
    return {"reply": reply, "model": model}, 200


class handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body_bytes.decode("utf-8") or "{}")

            res_body, status_code = process_chat(data)
            self._send_json(res_body, status=status_code)
        except HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                msg = json.loads(raw).get("error", {}).get("message", raw)
            except Exception:
                msg = raw
            self._send_json({"error": f"Gemini API error: {msg}"}, status=e.code or 502)
        except URLError as e:
            self._send_json({"error": f"Could not reach Gemini API: {e.reason}"}, status=502)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def do_GET(self):
        self._send_json({"status": "API is online. Send a POST request to chat."}, status=200)

