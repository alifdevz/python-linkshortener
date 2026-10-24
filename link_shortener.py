"""Server HTTP sederhana untuk menyimpan dan mengalihkan nama pendek ke URI panjang."""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse
from html import escape
import json
import os
import socket
import sqlite3
import string
import requests

# CSS dan JavaScript dipisah dari FORM karena FORM.format() menganggap { }
# sebagai placeholder. Kurung kurawal di dalam *nilai* yang disisipkan
# (style=STYLE, script=SCRIPT) tidak diproses oleh .format().
STYLE = """
  :root {
    color-scheme: light;
    --bg: #f4f6fb;
    --card: #ffffff;
    --text: #1f2937;
    --muted: #6b7280;
    --primary: #4f46e5;
    --primary-dark: #4338ca;
    --border: #d1d5db;
    --shadow: rgba(0, 0, 0, 0.08);
    --ring: rgba(79, 70, 229, 0.2);
    --danger: #dc2626;
    --success: #16a34a;
  }

  /* Mode sistem: ikuti pengaturan OS, kecuali pengguna memaksa tema terang */
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      color-scheme: dark;
      --bg: #0f172a;
      --card: #1e293b;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --primary: #818cf8;
      --primary-dark: #6366f1;
      --border: #334155;
      --shadow: rgba(0, 0, 0, 0.4);
      --ring: rgba(129, 140, 248, 0.35);
      --danger: #f87171;
      --success: #4ade80;
    }
  }

  /* Mode gelap yang dipilih manual lewat tombol */
  :root[data-theme="dark"] {
    color-scheme: dark;
    --bg: #0f172a;
    --card: #1e293b;
    --text: #e5e7eb;
    --muted: #9ca3af;
    --primary: #818cf8;
    --primary-dark: #6366f1;
    --border: #334155;
    --shadow: rgba(0, 0, 0, 0.4);
    --ring: rgba(129, 140, 248, 0.35);
    --danger: #f87171;
    --success: #4ade80;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 2rem 1rem;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    transition: background 0.2s, color 0.2s;
  }
  main { max-width: 560px; margin: 0 auto; }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  h1 { margin: 0; font-size: 1.6rem; }
  .card {
    background: var(--card);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 10px var(--shadow);
    margin-bottom: 1.5rem;
    transition: background 0.2s;
  }
  label { display: block; font-weight: 600; margin-bottom: 1rem; }
  input {
    display: block;
    width: 100%;
    margin-top: 0.4rem;
    padding: 0.65rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 1rem;
    background: var(--bg);
    color: var(--text);
  }
  input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--ring);
  }
  .message {
    min-height: 1.25rem;
    margin: 0;
    font-size: 0.9rem;
    color: var(--muted);
  }
  .message.error { color: var(--danger); }
  .message.success { color: var(--success); }
  .btn-secondary {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    margin-bottom: 0.75rem;
    padding: 0.7rem;
    border: 1.5px solid var(--primary);
    border-radius: 8px;
    background: transparent;
    color: var(--primary);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s, box-shadow 0.2s;
  }
  .btn-secondary:hover { background: var(--ring); }
  .btn-secondary:active { transform: translateY(1px); }
  .btn-secondary:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px var(--ring);
  }
  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
  .input-group { position: relative; margin-bottom: 1rem; }
  .input-group input { margin: 0; padding-right: 2.75rem; }
  .icon-btn {
    position: absolute;
    top: 50%;
    right: 0.4rem;
    transform: translateY(-50%);
    display: grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
  }
  .icon-btn:hover { background: var(--ring); color: var(--primary); }
  .icon-btn:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px var(--ring);
  }
  .icon-btn svg { width: 1.1rem; height: 1.1rem; }
  .icon-btn .icon-check { display: none; }
  .icon-btn.copied { color: var(--success); }
  .icon-btn.copied .icon-copy { display: none; }
  .icon-btn.copied .icon-check { display: block; }
  input[readonly] {
    border-style: dashed;
    background: transparent;
    cursor: text;
  }
  #theme-toggle {
    flex-shrink: 0;
    padding: 0.45rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card);
    color: var(--text);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
  }
  #theme-toggle:hover { border-color: var(--primary); }
  ul { list-style: none; margin: 0; padding: 0; }
  li {
    padding: 0.7rem 0;
    border-bottom: 1px solid var(--border);
    word-break: break-all;
  }
  li:last-child { border-bottom: 0; }
  li a { color: var(--primary); font-weight: 600; text-decoration: none; }
  li a:hover { text-decoration: underline; }
  li span { color: var(--muted); font-size: 0.9rem; display: block; }
  .empty { color: var(--muted); text-align: center; }
"""

SCRIPT = """
  (() => {
    const KEY = "theme";
    const MODES = ["system", "dark", "light"];
    const LABELS = {
      system: "🖥️ Sistem",
      dark: "🌙 Gelap",
      light: "☀️ Terang"
    };
    const root = document.documentElement;

    const getMode = () => {
      try {
        const saved = localStorage.getItem(KEY);
        if (MODES.includes(saved)) return saved;
      } catch {}
      return "system";
    };

    const applyMode = (mode) => {
      if (mode === "system") {
        root.removeAttribute("data-theme");
      } else {
        root.setAttribute("data-theme", mode);
      }
    };

    // Terapkan sedini mungkin supaya halaman tidak berkedip saat dimuat.
    let mode = getMode();
    applyMode(mode);

    document.addEventListener("DOMContentLoaded", () => {
      const btn = document.getElementById("theme-toggle");

      const render = () => {
        btn.textContent = LABELS[mode];
        btn.title = `Tema: ${LABELS[mode]} (klik untuk mengganti)`;
      };

      btn.addEventListener("click", () => {
        mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
        applyMode(mode);
        try { localStorage.setItem(KEY, mode); } catch {}
        render();
      });

      render();

      // --- Tombol salin nama pendek ---
      const shortInput = document.getElementById("shortname");
      const copyBtn = document.getElementById("copy-short");
      const COPY_TITLE = "Salin nama pendek";
      let copyTimer;

      const copyText = async (text) => {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch {
          // Cadangan untuk konteks tidak aman (misalnya http:// lewat IP LAN).
          shortInput.select();
          try { return document.execCommand("copy"); } catch { return false; }
        }
      };

      copyBtn.addEventListener("click", async () => {
        if (!shortInput.value) {
          shortInput.focus();
          return;
        }
        const ok = await copyText(shortInput.value);
        copyBtn.classList.toggle("copied", ok);
        copyBtn.title = ok ? "Tersalin!" : "Gagal menyalin";

        clearTimeout(copyTimer);
        copyTimer = setTimeout(() => {
          copyBtn.classList.remove("copied");
          copyBtn.title = COPY_TITLE;
        }, 1500);
      });

      // --- Tombol generate tautan pendek ---
      const form = document.getElementById("shorten-form");
      const longInput = document.getElementById("longuri");
      const generateBtn = document.getElementById("generate-short");
      const generateLabel = generateBtn.querySelector(".btn-label");
      const GENERATE_TITLE = generateLabel.textContent;
      const message = document.getElementById("message");
      const listSection = document.getElementById("link-list");

      const showMessage = (text, type = "") => {
        message.textContent = text;
        message.className = type ? `message ${type}` : "message";
      };

      // Tambahkan link baru ke daftar tanpa memuat ulang halaman.
      const addToList = (code, longuri) => {
        let list = document.getElementById("link-items");
        if (!list) {
          list = document.createElement("ul");
          list.id = "link-items";
          const empty = document.getElementById("empty-msg");
          if (empty) empty.replaceWith(list);
          else listSection.appendChild(list);
        }
        if (list.querySelector(`[data-code="${code}"]`)) return;

        const li = document.createElement("li");
        li.dataset.code = code;
        const a = document.createElement("a");
        a.href = `/${code}`;
        a.textContent = a.href;
        const span = document.createElement("span");
        span.textContent = longuri;
        li.append(a, span);
        list.prepend(li);
      };

      const generate = async () => {
        if (!longInput.reportValidity()) return;

        generateBtn.disabled = true;
        generateLabel.textContent = "Memproses...";
        showMessage("");

        try {
          const res = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ longuri: longInput.value.trim() })
          });
          const data = await res.json().catch(() => ({}));

          if (!res.ok) {
            shortInput.value = "";
            showMessage(data.error || "Terjadi kesalahan pada server.", "error");
            return;
          }

          // --- Ketika berhasil, tampilkan nama pendek dan tambahkan ke daftar beserta scheme dan host-nya. ---
          shortInput.value = window.origin + "/" + data.shortname;
          addToList(data.shortname, data.longuri);
          showMessage(
            data.created
              ? "Nama pendek berhasil dibuat."
              : "URL ini sudah pernah dipendekkan, memakai nama yang sama.",
            "success"
          );
        } catch {
          shortInput.value = "";
          showMessage("Tidak dapat terhubung ke server.", "error");
        } finally {
          generateBtn.disabled = false;
          generateLabel.textContent = GENERATE_TITLE;
        }
      };

      // --- Tautan pendek di daftar (ketika halaman di-refresh tampilkan semua short link dengan lengkap mencakup scheme dan host-nya) ---
      document.querySelectorAll("#link-items a").forEach((a) => {
        a.textContent = a.href;
      });

      generateBtn.addEventListener("click", generate);
      longInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          generate();
        }
      });
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        generate();
      });
    });
  })();
"""

FORM = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Link Shortener</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27><text y=%27.9em%27 font-size=%2790%27>🔗</text></svg>">
  <style>{style}</style>
  <script>{script}</script>
</head>
<body>
  <main>
    <header>
      <h1>🔗 Link Shortener</h1>
      <button type="button" id="theme-toggle">Tema</button>
    </header>

    <form id="shorten-form" class="card">
      <label>URL panjang
        <input type="url" name="longuri" id="longuri" placeholder="https://contoh.com/halaman/panjang" required>
      </label>
      <button type="button" name="generate" id="generate-short" class="btn-secondary">
        <span aria-hidden="true">🎲</span> <span class="btn-label">Generate tautan pendek</span>
      </button>
      <div class="input-group">
        <input type="text" name="shortname" id="shortname" placeholder="contoh" readonly>
        <button type="button" id="copy-short" class="icon-btn" title="Salin nama pendek" aria-label="Salin nama pendek">
          <svg class="icon-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="9" y="9" width="13" height="13" rx="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <svg class="icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
      </div>
      <p id="message" class="message" role="status" aria-live="polite"></p>
    </form>

    <section class="card" id="link-list">
      <h2>Daftar link</h2>
      {known}
    </section>
  </main>
</body>
</html>
"""

# =====================================================================
# DATABASE SQLITE & BASE62
# =====================================================================
DATABASE_FILE = "url_shortener.db"

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


def init_database():
    """Membuat file database dan tabel 'urls' jika belum ada.

    Kolom 'long_url' bersifat UNIQUE agar URL yang sama tidak tersimpan dua kali.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
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
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO urls (long_url) VALUES (?)", (long_url,))
            conn.commit()
            assigned_id = cursor.lastrowid
            if assigned_id is None:
                raise sqlite3.DatabaseError("Gagal memperoleh ID URL baru")
            created = True
        except sqlite3.IntegrityError as exc:
            cursor.execute("SELECT id FROM urls WHERE long_url = ?", (long_url,))
            row = cursor.fetchone()
            if row is None:
                raise sqlite3.DatabaseError("URL tidak ditemukan setelah pelanggaran UNIQUE") from exc
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

    conn = sqlite3.connect(DATABASE_FILE)
    try:
        row = conn.execute(
            "SELECT long_url FROM urls WHERE id = ?", (db_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def list_links():
    """Daftar (kode_pendek, url_panjang), yang terbaru di paling atas."""
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        rows = conn.execute(
            "SELECT id, long_url FROM urls ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()
    return [(id_to_code(row_id), long_url) for row_id, long_url in rows]


def render_links():
    """Buat HTML untuk daftar link. escape() mencegah XSS."""
    rows = list_links()
    if not rows:
        return '<p class="empty" id="empty-msg">Belum ada link tersimpan.</p>'

    items = "\n".join(
        f'<li data-code="{escape(code)}"><a href="/{escape(code)}">/{escape(code)}</a>'
        f"<span>{escape(long_url)}</span></li>"
        for code, long_url in rows
    )
    return f'<ul id="link-items">{items}</ul>'


def validate_long_url(url: str):
    """Kembalikan pesan error jika URL tidak valid, atau None jika valid."""
    if not url:
        return "URL tidak boleh kosong."
    if len(url) > MAX_URL_LENGTH:
        return "URL terlalu panjang."
    if any(c.isspace() or ord(c) < 32 for c in url):
        return "URL tidak boleh mengandung spasi atau karakter kontrol."
    try:
        parsed = urlparse(url)
    except ValueError:
        return "URL tidak valid."
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "URL harus diawali dengan http:// atau https://"
    return None


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

    def do_GET(self):  # pylint: disable=invalid-name
        """Handle requests for the form or to resolve a short link."""
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        shortname = unquote(self.path[1:])

        if shortname:
            long_url = get_original_url(shortname)
            if long_url:
                self.send_response(303)
                self.send_header("Location", long_url)
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"I don't know {shortname}.".encode())
        else:
            # Root path. Send the form.
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            page = FORM.format(style=STYLE, script=SCRIPT, known=render_links())
            self.wfile.write(page.encode())

    def do_POST(self):  # pylint: disable=invalid-name
        """Generate a short URL from the JSON-compatible form request."""
        # Satu-satunya rute POST: /generate (dipanggil lewat fetch dari browser).
        if self.path != "/generate":
            self.send_json(404, {"error": "Rute tidak ditemukan."})
            return

        # How long was the message? (Use the Content-Length header.)
        try:
            length = int(self.headers.get("Content-length", 0))
        except ValueError:
            length = 0
        if length > MAX_URL_LENGTH * 4:
            self.send_json(413, {"error": "Permintaan terlalu besar."})
            return

        body = self.rfile.read(length).decode(errors="replace")
        params = parse_qs(body)
        longuri = params.get("longuri", [""])[0].strip()

        error = validate_long_url(longuri)
        if error:
            self.send_json(400, {"error": error})
            return

        if not check_uri(longuri):
            self.send_json(
                422, {"error": "URL tidak dapat diakses (harus membalas 200 OK)."}
            )
            return

        code, created = shorten_url(longuri)
        self.send_json(
            201 if created else 200,
            {"shortname": code, "longuri": longuri, "created": created},
        )


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


if __name__ == "__main__":
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