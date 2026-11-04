import asyncio
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

import edge_tts


ALLOWED_ORIGINS = {
    "https://kho-tu-kho.vercel.app",
    "https://thunopro.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}
# Thêm giọng mới: thêm một mục vào VOICES. Giao diện tự lấy danh sách qua ?voices=1.
VOICES = {
    "uk": {"voice": "en-GB-SoniaNeural", "label": "Anh-Anh (UK)"},
    "us": {"voice": "en-US-AriaNeural", "label": "Anh-Mỹ (US)"},
}


class handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Expose-Headers", "X-Pronunciation-Voice")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _json_error(self, status, message):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        if "voices" in query:
            voices = [{"value": key, "label": item["label"]} for key, item in VOICES.items()]
            return self._json(200, {"voices": voices})

        text = query.get("text", [""])[0].strip()
        accent = query.get("accent", ["uk"])[0].lower()

        if not text:
            return self._json_error(400, "Nhập từ hoặc cụm từ tiếng Anh trước.")
        if len(text) > 80:
            return self._json_error(400, "Mỗi lần chỉ đọc tối đa 80 ký tự.")
        if accent not in VOICES:
            return self._json_error(400, "Giọng đọc chỉ hỗ trợ UK hoặc US.")
        if any(ord(char) < 32 for char in text):
            return self._json_error(400, "Nội dung có ký tự không hợp lệ.")

        voice = VOICES[accent]["voice"]
        try:
            audio = asyncio.run(self._synthesize(text, voice))
        except Exception:
            return self._json_error(502, "Dịch vụ giọng đọc đang bận. Vui lòng thử lại.")

        if not audio:
            return self._json_error(502, "Dịch vụ chưa tạo được âm thanh cho từ này.")

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", str(len(audio)))
        self.send_header("Cache-Control", "public, max-age=86400, s-maxage=86400")
        self.send_header("X-Pronunciation-Voice", voice)
        self.end_headers()
        self.wfile.write(audio)

    @staticmethod
    async def _synthesize(text, voice):
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="-8%",
            connect_timeout=10,
            receive_timeout=20,
        )
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)
