"""Server HTTP sederhana untuk menyimpan dan mengalihkan nama pendek ke URI panjang."""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, quote
from html import escape
import os
import socket
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
  button[type="submit"] {
    width: 100%;
    padding: 0.75rem;
    border: 0;
    border-radius: 8px;
    background: var(--primary);
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  button[type="submit"]:hover { background: var(--primary-dark); }
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
  (function () {
    var KEY = "theme";
    var MODES = ["system", "dark", "light"];
    var LABELS = {
      system: "🖥️ Sistem",
      dark: "🌙 Gelap",
      light: "☀️ Terang"
    };
    var root = document.documentElement;

    function getMode() {
      try {
        var saved = localStorage.getItem(KEY);
        if (MODES.indexOf(saved) !== -1) return saved;
      } catch (e) {}
      return "system";
    }

    function applyMode(mode) {
      if (mode === "system") {
        root.removeAttribute("data-theme");
      } else {
        root.setAttribute("data-theme", mode);
      }
    }

    // Terapkan sedini mungkin supaya halaman tidak berkedip saat dimuat.
    var mode = getMode();
    applyMode(mode);

    document.addEventListener("DOMContentLoaded", function () {
      var btn = document.getElementById("theme-toggle");

      function render() {
        btn.textContent = LABELS[mode];
        btn.title = "Tema: " + LABELS[mode] + " (klik untuk mengganti)";
      }

      btn.addEventListener("click", function () {
        mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
        applyMode(mode);
        try { localStorage.setItem(KEY, mode); } catch (e) {}
        render();
      });

      render();
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

    <form method="POST" class="card">
      <label>URL panjang
        <input type="url" name="longuri" placeholder="https://contoh.com/halaman/panjang" required>
      </label>
      <label>Nama pendek
        <input type="text" name="shortname" placeholder="contoh" required>
      </label>
      <button type="submit">Simpan</button>
    </form>

    <section class="card">
      <h2>Daftar link</h2>
      {known}
    </section>
  </main>
</body>
</html>
"""

memory = {}


def check_uri(uri, timeout=5):
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

    def do_GET(self):
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        shortname = unquote(self.path[1:])

        if shortname:
            if shortname in memory:
                self.send_response(303)
                self.send_header("Location", memory[shortname])
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

            if memory:
                # escape() mencegah XSS; quote() membuat URL valid
                # untuk nama pendek yang mengandung spasi/karakter khusus.
                items = "\n".join(
                    f'<li><a href="/{quote(key)}">/{escape(key)}</a>'
                    f"<span>{escape(value)}</span></li>"
                    for key, value in memory.items()
                )
                known = f"<ul>{items}</ul>"
            else:
                known = '<p class="empty">Belum ada link tersimpan.</p>'

            self.wfile.write(FORM.format(style=STYLE, script=SCRIPT, known=known).encode())

    def do_POST(self):
        # How long was the message? (Use the Content-Length header.)
        length = int(self.headers.get("Content-length", 0))

        # Read the correct amount of data from the request and decode it
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        if "longuri" not in params or "shortname" not in params:
            # Extract the "longuri" and "shortname" fields from the request data.
            self.send_response(400)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Error 400: Bad request!".encode())
            return

        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if check_uri(longuri):
            # This URI is good!  Remember it under the specified name.
            memory[shortname] = longuri

            # Serve a redirect to the root page (the form).
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Error 404: Not found!".encode())


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