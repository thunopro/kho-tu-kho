import hashlib
import hmac
import json
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import urllib.request


ALLOWED_ORIGINS = {
    "https://kho-tu-kho.vercel.app",
    "https://thunopro.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}
MAX_WORDS = 1000           # tổng số từ trong một kho
MAX_FILES = 100            # tổng số file (mỗi file chứa nhiều từ)
MAX_FOLDERS = 60           # tổng số thư mục trong một kho
MAX_DEPTH = 4              # số cấp thư mục lồng nhau tối đa
MAX_FOLDER_NAME = 40
MAX_WORD_LENGTH = 80
MAX_BODY_BYTES = 256 * 1024
ID_PATTERN = re.compile(r"^[1-9][0-9]{0,17}$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
# Bảng "kho" đã tồn tại từ phiên bản đầu (cột words = danh sách phẳng).
# Không xóa bảng cũ: thêm cột tree và cho phép words rỗng; dữ liệu cũ được
# đọc như một file "Từ vựng" ở gốc (xem legacy_tree).
SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS kho (
        id BIGSERIAL PRIMARY KEY,
        key_hash TEXT NOT NULL,
        words JSONB,
        tree JSONB,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "ALTER TABLE kho ADD COLUMN IF NOT EXISTS tree JSONB",
    "ALTER TABLE kho ALTER COLUMN words DROP NOT NULL",
]
VOCAB_FILE = "Từ vựng"
_schema_ready = False


def _run(query, params=None):
    dsn = os.environ["DATABASE_URL"]
    host = urlsplit(dsn).hostname
    request = urllib.request.Request(
        f"https://{host}/sql",
        data=json.dumps({"query": query, "params": params or []}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Neon-Connection-String": dsn,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8")).get("rows", [])


def sql(query, params=None):
    """Run one SQL statement through Neon's HTTP endpoint and return its rows."""
    global _schema_ready
    if not _schema_ready:
        for statement in SCHEMA_STATEMENTS:
            _run(statement)
        _schema_ready = True
    return _run(query, params)


def legacy_tree(words):
    """Chuyển danh sách phẳng cũ thành cây: một file "Từ vựng" ở gốc."""
    items = load_json(words) or []
    word_items = [
        {"word": item["word"], "addedAt": int(item.get("addedAt", 0) or 0)}
        for item in items
        if isinstance(item, dict) and isinstance(item.get("word"), str)
    ]
    if not word_items:
        return []
    return [{"type": "file", "name": VOCAB_FILE, "words": word_items}]


def hash_key(key):
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def load_json(value):
    return json.loads(value) if isinstance(value, str) else value


def clean_name(raw, max_length, label):
    if not isinstance(raw, str):
        raise ValueError(f"{label} không hợp lệ.")
    name = re.sub(r"\s+", " ", raw).strip()
    if not name or len(name) > max_length or name in (".", ".."):
        raise ValueError(f"{label} phải có từ 1 đến {max_length} ký tự.")
    if "/" in name or CONTROL_CHARS.search(name):
        raise ValueError(f"{label} chứa ký tự không hợp lệ.")
    return name


class TreeLimits:
    def __init__(self):
        self.files = 0
        self.folders = 0
        self.words = 0


def sanitize_words(raw_words, limits):
    if not isinstance(raw_words, list):
        raise ValueError("Dữ liệu kho không hợp lệ.")
    seen = set()
    cleaned = []
    for raw in raw_words:
        if not isinstance(raw, dict):
            raise ValueError("Dữ liệu kho không hợp lệ.")
        word = clean_name(raw.get("word"), MAX_WORD_LENGTH, "Mỗi từ")
        if word.lower() in seen:
            continue
        seen.add(word.lower())
        limits.words += 1
        if limits.words > MAX_WORDS:
            raise ValueError(f"Kho tối đa {MAX_WORDS} từ.")
        added_at = raw.get("addedAt")
        cleaned.append({"word": word, "addedAt": int(added_at) if isinstance(added_at, (int, float)) else 0})
    return cleaned


def sanitize_children(raw_children, depth, limits):
    if not isinstance(raw_children, list):
        raise ValueError("Dữ liệu kho không hợp lệ.")
    seen = set()
    cleaned = []
    for raw in raw_children:
        if not isinstance(raw, dict):
            raise ValueError("Dữ liệu kho không hợp lệ.")
        kind = raw.get("type")
        if kind == "dir":
            if depth > MAX_DEPTH:
                raise ValueError(f"Thư mục chỉ được lồng tối đa {MAX_DEPTH} cấp.")
            name = clean_name(raw.get("name"), MAX_FOLDER_NAME, "Tên thư mục")
            limits.folders += 1
            if limits.folders > MAX_FOLDERS:
                raise ValueError(f"Kho tối đa {MAX_FOLDERS} thư mục.")
            node = {
                "type": "dir",
                "name": name,
                "children": sanitize_children(raw.get("children", []), depth + 1, limits),
            }
        elif kind == "file":
            name = clean_name(raw.get("name"), MAX_FOLDER_NAME, "Tên file")
            limits.files += 1
            if limits.files > MAX_FILES:
                raise ValueError(f"Kho tối đa {MAX_FILES} file.")
            node = {
                "type": "file",
                "name": name,
                "words": sanitize_words(raw.get("words", []), limits),
            }
        else:
            raise ValueError("Dữ liệu kho không hợp lệ.")
        key = node["name"].lower()
        if key in seen:
            raise ValueError(f"Trùng tên “{node['name']}” trong cùng thư mục.")
        seen.add(key)
        cleaned.append(node)
    return cleaned


def sanitize_tree(raw_tree):
    limits = TreeLimits()
    children = sanitize_children(raw_tree, 1, limits)
    if limits.words == 0:
        raise ValueError("Kho cần có ít nhất một từ để publish.")
    return children


class handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        kho_id = query.get("id", [""])[0]
        if not ID_PATTERN.match(kho_id):
            return self._json(400, {"error": "Số ID kho không hợp lệ."})
        try:
            rows = sql("SELECT tree, words FROM kho WHERE id = $1", [int(kho_id)])
        except Exception:
            return self._json(503, {"error": "Máy chủ kho đang bận. Vui lòng thử lại."})
        if not rows:
            return self._json(404, {"error": "Kho này chưa được publish."})
        if rows[0]["tree"] is not None:
            tree = load_json(rows[0]["tree"])
        else:
            tree = legacy_tree(rows[0]["words"])
        return self._json(200, {"id": kho_id, "tree": tree})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > MAX_BODY_BYTES:
            return self._json(413, {"error": f"Dữ liệu quá lớn. Kho tối đa {MAX_WORDS} từ."})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "Dữ liệu gửi lên không hợp lệ."})
        if not isinstance(body, dict) or body.get("action") != "publish":
            return self._json(400, {"error": "Thao tác không được hỗ trợ."})

        try:
            tree = sanitize_tree(body.get("tree"))
        except ValueError as error:
            return self._json(400, {"error": str(error)})

        payload = json.dumps(tree, ensure_ascii=False)
        kho_id = str(body.get("id") or "")
        key = str(body.get("key") or "")
        try:
            if kho_id and key:
                if not ID_PATTERN.match(kho_id):
                    return self._json(400, {"error": "Số ID kho không hợp lệ."})
                rows = sql("SELECT key_hash FROM kho WHERE id = $1", [int(kho_id)])
                if not rows or not hmac.compare_digest(rows[0]["key_hash"], hash_key(key)):
                    return self._json(403, {"error": "Không có quyền cập nhật kho này trên máy này."})
                sql(
                    "UPDATE kho SET tree = $1::jsonb, updated_at = now() WHERE id = $2",
                    [payload, int(kho_id)],
                )
                return self._json(200, {"id": kho_id})

            new_key = secrets.token_urlsafe(32)
            rows = sql(
                "INSERT INTO kho (key_hash, tree) VALUES ($1, $2::jsonb) RETURNING id",
                [hash_key(new_key), payload],
            )
            return self._json(201, {"id": str(rows[0]["id"]), "key": new_key})
        except Exception:
            return self._json(503, {"error": "Máy chủ kho đang bận. Vui lòng thử lại."})
