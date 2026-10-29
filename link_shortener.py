"""Server HTTP sederhana untuk menyimpan dan mengalihkan nama pendek ke URI panjang."""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse
from html import escape
from pathlib import Path
import json
import importlib
import os
import socket
import sqlite3
import string
import traceback
from typing import Any, cast
import requests

try:
    # hanya diperlukan jika DATABASE_URL (PostgreSQL) dipakai
    psycopg = importlib.import_module("psycopg")
except ImportError:
    psycopg = None

# =====================================================================
# TAMPILAN: template HTML (templates/) dan file statis CSS/JS (static/)
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Hanya nama file di daftar ini yang dilayani lewat /static/<nama>. Nama dicocokkan
# persis (bukan disambung ke path), sehingga file di luar folder tidak bisa dibaca.
STATIC_FILES = {
    "style.css": "text/css; charset=utf-8",
    "i18n.js": "text/javascript; charset=utf-8",
    "theme.js": "text/javascript; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}


def load_template(name: str) -> str:
    """Baca template HTML dari folder templates/ (sekali, saat server dimulai)."""
    return (BASE_DIR / "templates" / name).read_text(encoding="utf-8")


INDEX_HTML = load_template("index.html")
NOT_FOUND_HTML = load_template("not_found.html")


# =====================================================================
# DATABASE (PostgreSQL jika DATABASE_URL diatur, selain itu SQLite) & BASE62
# =====================================================================
# Di Render, filesystem bersifat sementara sehingga file SQLite hilang setiap
# deploy. Atur environment variable DATABASE_URL (misalnya dari Neon) agar data
# disimpan di PostgreSQL eksternal. Tanpa DATABASE_URL, SQLite lokal dipakai
# (cocok untuk pengembangan di komputer sendiri).
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DATABASE_FILE = "url_shortener.db"

# Kelas error "melanggar UNIQUE" untuk kedua jenis database.
INTEGRITY_ERRORS = (sqlite3.IntegrityError,) + (
  (cast(type[Exception], getattr(psycopg, "IntegrityError")),) if psycopg else ()
)

# Karakter Base62: total 62 karakter unik (0-9, a-z, A-Z)
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase

MAX_URL_LENGTH = 2048

# Kode pendek selalu CODE_LENGTH karakter. ID database tidak dipakai langsung,
# tetapi diacak dulu secara reversibel (bijeksi pada ruang 0..SPACE-1):
#     kode = encode((id * MULTIPLIER + OFFSET) mod SPACE)
# Agar tiap ID punya kode unik, MULTIPLIER harus koprima dengan SPACE.
# SPACE = 2**6 * 31**6, jadi MULTIPLIER harus ganjil dan bukan kelipatan 31.
# PENTING: jangan ubah CODE_LENGTH, MULTIPLIER, dan OFFSET setelah ada link
# yang dibuat, karena semua kode lama akan berubah dan tidak bisa dibuka lagi.
CODE_LENGTH = 6
SPACE = len(BASE62) ** CODE_LENGTH
MULTIPLIER = 41_237_905_113
OFFSET = 27_182_818_284
# Invers perkalian modular (pow melempar ValueError jika tidak koprima).
MULTIPLIER_INVERSE = pow(MULTIPLIER, -1, SPACE)


def connect_db():
    """Buka koneksi baru: PostgreSQL jika DATABASE_URL diatur, selain itu SQLite."""
    if DATABASE_URL:
        if psycopg is None:
            raise RuntimeError(
                'DATABASE_URL diatur, tetapi psycopg belum terpasang '
                '(pip install "psycopg[binary]").'
            )
        return psycopg.connect(DATABASE_URL, connect_timeout=10)
    return sqlite3.connect(DATABASE_FILE)


def run(conn: Any, sql: str, params: tuple[Any, ...] = ()):
    """Jalankan query. Placeholder ditulis '?' dan diubah ke '%s' untuk PostgreSQL."""
    if DATABASE_URL:
        sql = sql.replace("?", "%s")
    return conn.execute(sql, params)


def init_database():
    """Membuat tabel 'urls' jika belum ada.

    Kolom 'long_url' bersifat UNIQUE agar URL yang sama tidak tersimpan dua kali.
    """
    if DATABASE_URL:
        id_column = "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
    else:
        id_column = "INTEGER PRIMARY KEY AUTOINCREMENT"

    conn = connect_db()
    try:
        run(
            conn,
            f"""
            CREATE TABLE IF NOT EXISTS urls (
                id {id_column},
                long_url TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        conn.commit()
    finally:
        conn.close()


def encode_base62(num: int) -> str:
    """Mengubah angka ID database menjadi string pendek Base62."""
    if num == 0:
        return BASE62[0]

    arr: list[str] = []
    base = len(BASE62)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])
    arr.reverse()
    return "".join(arr)


def decode_base62(short_str: str):
    """Mengubah string Base62 kembali menjadi angka ID database.

    Melempar ValueError jika ada karakter di luar Base62.
    """
    base = len(BASE62)
    num = 0
    for char in short_str:
        index = BASE62.find(char)
        if index == -1:
            raise ValueError(f"Karakter tidak valid: {char!r}")
        num = num * base + index
    return num


def id_to_code(db_id: int):
    """ID database -> kode pendek yang tampak acak (selalu CODE_LENGTH karakter)."""
    if not 0 <= db_id < SPACE:
        raise ValueError("ID di luar jangkauan kode pendek.")
    scrambled = (db_id * MULTIPLIER + OFFSET) % SPACE
    return encode_base62(scrambled).rjust(CODE_LENGTH, BASE62[0])


def code_to_id(code: str):
    """Kebalikan dari id_to_code. Melempar ValueError jika kode tidak valid."""
    if len(code) != CODE_LENGTH:
        raise ValueError("Panjang kode tidak sesuai.")
    scrambled = decode_base62(code)
    return ((scrambled - OFFSET) * MULTIPLIER_INVERSE) % SPACE


def shorten_url(long_url: str) -> tuple[str, bool]:
    """Simpan URL ke database lalu kembalikan (kode_pendek, baru_dibuat).

    Jika URL sudah ada (melanggar UNIQUE), ID lama dipakai kembali.
    """
    conn = connect_db()
    try:
        try:
            if DATABASE_URL:
                row = run(
                    conn,
                    "INSERT INTO urls (long_url) VALUES (?) RETURNING id",
                    (long_url,),
                ).fetchone()
                assigned_id = row[0]
            else:
                cursor = run(conn, "INSERT INTO urls (long_url) VALUES (?)", (long_url,))
                assigned_id = cursor.lastrowid
            conn.commit()
            if assigned_id is None:
                raise RuntimeError("Gagal memperoleh ID URL baru")
            created = True
        except INTEGRITY_ERRORS as exc:
            # PostgreSQL membatalkan transaksi setelah error, jadi rollback dulu.
            conn.rollback()
            row = run(
                conn, "SELECT id FROM urls WHERE long_url = ?", (long_url,)
            ).fetchone()
            if row is None:
                raise RuntimeError(
                    "URL tidak ditemukan setelah pelanggaran UNIQUE"
                ) from exc
            assigned_id = row[0]
            created = False
    finally:
        conn.close()

    return id_to_code(assigned_id), created


def get_original_url(short_code: str):
    """Decode kode pendek dan cari URL aslinya. Kembalikan None jika tidak ada."""
    try:
        db_id = code_to_id(short_code)
    except ValueError:
        return None

    conn = connect_db()
    try:
        row = run(conn, "SELECT long_url FROM urls WHERE id = ?", (db_id,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


# Kode error API. Browser menerjemahkan kode ini sesuai bahasa pilihan pengguna
# (kunci "err.<kode>" di static/i18n.js); teks Inggris ini dipakai sebagai cadangan
# dan untuk klien non-browser. Jaga agar kedua tempat tetap sinkron.
ERRORS = {
    "url_empty": "The URL must not be empty.",
    "url_too_long": "The URL is too long.",
    "url_bad_chars": "The URL must not contain spaces or control characters.",
    "url_invalid": "The URL is not valid.",
    "url_scheme": "The URL must start with http:// or https://",
    "url_unreachable": "The URL could not be reached (it must respond with 200 OK).",
    "request_too_large": "The request is too large.",
    "route_not_found": "Route not found.",
    "db_unavailable": "The database is temporarily unavailable. Please try again shortly.",
    "link_empty": "The short link must not be empty.",
    "link_invalid": "The short link format is not valid.",
    "link_foreign": "This link does not belong to this service.",
    "link_not_found": "Short link not found.",
}


def validate_long_url(url: str):
    """Kembalikan kode error (kunci ERRORS) jika URL tidak valid, atau None jika valid."""
    if not url:
        return "url_empty"
    if len(url.encode("utf-8")) > MAX_URL_LENGTH:
        return "url_too_long"
    if any(c.isspace() or ord(c) < 32 for c in url):
        return "url_bad_chars"
    try:
        parsed = urlparse(url)
    except ValueError:
        return "url_invalid"
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "url_scheme"
    return None


def extract_short_code(text: str):
    """Ambil (host, kode) dari input pengguna, atau None jika tidak dapat diuraikan.

    Menerima 'https://host/kode', 'host/kode', '/kode', atau 'kode'.
    Host berupa string kosong jika tidak disertakan.
    """
    if "://" not in text and "/" in text and not text.startswith("/"):
        text = "//" + text  # 'host/kode' -> urlparse mengenali host
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    return parsed.netloc, parsed.path.strip("/")


def check_uri(uri: str, timeout: float = 5):
    """
    Check whether this URI is reachable, i.e. does it return a 200 OK?"""
    try:
        r = requests.get(uri, timeout=timeout)
        # If the GET request returns, was it a 200 OK?
        return r.status_code == 200
    except requests.RequestException:
        # If the GET request raised an exception, it's not OK.
        return False


class LinkShortener(BaseHTTPRequestHandler):
    """Handle HTTP requests for creating and resolving short links.

    This is an HTTPServer that supports thread-based concurrency.
    """

    def send_json(self, status: int, payload: dict[str, object]):
        """Send a JSON response with the given status and payload."""
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_api_error(self, status: int, code: str):
        """Kirim error JSON berisi kode (untuk diterjemahkan browser) dan teks Inggris."""
        self.send_json(status, {"error": ERRORS[code], "code": code})

    def db_unavailable(self, as_json: bool = False):
        """Balas 503 ketika database tidak dapat diakses (error dicetak ke log)."""
        traceback.print_exc()
        message = ERRORS["db_unavailable"]
        if as_json:
            self.send_api_error(503, "db_unavailable")
        else:
            self.send_response(503)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(message.encode())

    def get_base_url(self) -> str:
        """Alamat dasar yang dipakai pengunjung: scheme://host[:port]."""
        # Di balik proxy (seperti Render), SSL diakhiri oleh proxy sehingga
        # skema asli dikirim lewat header X-Forwarded-Proto.
        forwarded = self.headers.get("X-Forwarded-Proto", "http")
        scheme = forwarded.split(",")[0].strip().lower()
        if scheme not in ("http", "https"):
            scheme = "http"
        # Tanpa header Host, pakai port tempat koneksi ini diterima.
        port = self.connection.getsockname()[1]
        host = self.headers.get("Host") or f"localhost:{port}"
        return f"{scheme}://{host}"

    def send_static(self, name: str):
        """Sajikan file dari folder static/ (hanya nama di STATIC_FILES)."""
        content_type = STATIC_FILES.get(name)
        file_path = STATIC_DIR / name
        try:
            if content_type is None:
                raise FileNotFoundError(name)
            stat = file_path.stat()
        except OSError:
            self.send_response(404)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        # ETag + no-cache: browser selalu memeriksa versi terbaru, tetapi cukup
        # mendapat balasan 304 (tanpa isi) kalau file belum berubah.
        etag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("ETag", etag)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def send_not_found(self, shortname: str):
        """Balas 404 dengan halaman HTML yang senada dengan halaman utama."""
        # Batasi panjang yang ditampilkan; escape() mencegah XSS dari path/header.
        link = f"{self.get_base_url()}/{shortname}"
        shown = link if len(link) <= 200 else link[:200] + "…"
        page = NOT_FOUND_HTML.replace("{link}", escape(shown))
        data = page.encode()
        self.send_response(404)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # pylint: disable=invalid-name
        """Handle requests for the form or to resolve a short link."""
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        path = urlparse(self.path).path
        if path.startswith("/static/"):
            self.send_static(path[len("/static/"):])
            return

        shortname = unquote(self.path[1:])

        if shortname:
            try:
                long_url = get_original_url(shortname)
            except Exception:  # pylint: disable=broad-exception-caught
                self.db_unavailable()
                return
            if long_url:
                self.send_response(303)
                self.send_header("Location", long_url)
                self.end_headers()
            else:
                self.send_not_found(shortname)
        else:
            # Root path. Send the form.
            page = INDEX_HTML
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode())

    def read_form(self):
        """Baca badan form. Kembalikan None (dan balas 413) jika terlalu besar."""
        # How long was the message? (Use the Content-Length header.)
        try:
            length = int(self.headers.get("Content-length", 0))
        except ValueError:
            length = 0
        if length > MAX_URL_LENGTH * 4:
            self.send_api_error(413, "request_too_large")
            return None

        body = self.rfile.read(length).decode(errors="replace")
        return parse_qs(body)

    def do_POST(self):  # pylint: disable=invalid-name
        """Rute POST: /generate (buat link pendek) dan /verify (cari URL asli)."""
        handlers = {"/generate": self.handle_generate, "/verify": self.handle_verify}
        handler = handlers.get(self.path)
        if handler is None:
            self.send_api_error(404, "route_not_found")
            return

        params = self.read_form()
        if params is not None:
            handler(params)

    def handle_generate(self, params: dict[str, list[str]]):
        """Buat link pendek dari URL panjang (dipanggil lewat fetch dari browser)."""
        longuri = params.get("longuri", [""])[0].strip()

        error = validate_long_url(longuri)
        if error:
            self.send_api_error(400, error)
            return

        if not check_uri(longuri):
            self.send_api_error(422, "url_unreachable")
            return

        try:
            code, created = shorten_url(longuri)
        except Exception:  # pylint: disable=broad-exception-caught
            self.db_unavailable(as_json=True)
            return
        self.send_json(
            201 if created else 200,
            {"shortname": code, "longuri": longuri, "created": created},
        )

    def handle_verify(self, params: dict[str, list[str]]):
        """Cari URL asli dari link pendek tanpa mengalihkan pengguna."""
        text = params.get("shortlink", [""])[0].strip()
        if not text:
            self.send_api_error(400, "link_empty")
            return

        parts = None
        if len(text.encode("utf-8")) <= MAX_URL_LENGTH and not any(
            c.isspace() or ord(c) < 32 for c in text
        ):
            parts = extract_short_code(text)
        if parts is None:
            self.send_api_error(400, "link_invalid")
            return

        host, code = parts
        # Link dari domain lain tidak boleh "terverifikasi" oleh layanan ini.
        if host and host.lower() != self.headers.get("Host", "").lower():
            self.send_api_error(400, "link_foreign")
            return

        try:
            long_url = get_original_url(code)
        except Exception:  # pylint: disable=broad-exception-caught
            self.db_unavailable(as_json=True)
            return
        if not long_url:
            self.send_api_error(404, "link_not_found")
            return
        self.send_json(200, {"code": code, "longuri": long_url})


class DualStackServer(ThreadingHTTPServer):
    """Server multi-thread yang menerima koneksi IPv6 dan IPv4 sekaligus."""

    address_family = socket.AF_INET6

    def server_bind(self):
        # Izinkan koneksi IPv4 juga pada socket IPv6 (dual-stack).
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


def main():
    """Siapkan database, jalankan server, dan tampilkan alamatnya."""
    try:
        init_database()

        # Use environment PORT if it is available. If not, use 8000
        port = int(os.environ.get("PORT", 8000))
        try:
            # Serve on all addresses (IPv6 + IPv4)
            httpd = DualStackServer(("::", port), LinkShortener)
        except OSError:
            # Sistem tidak mendukung IPv6: pakai IPv4 saja.
            httpd = ThreadingHTTPServer(("0.0.0.0", port), LinkShortener)

        host, port = httpd.socket.getsockname()[:2]
        url_host = f"[{host}]" if ":" in host else host
        print(f"Serving HTTP on {host} port {port} (http://{url_host}:{port}/) ...")

        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interruption. The program is stopped by user!")


if __name__ == "__main__":
    main()
