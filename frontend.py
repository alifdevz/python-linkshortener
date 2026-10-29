"""Tampilan (front-end) aplikasi link shortener: CSS, JavaScript, dan template HTML.

Semua konstanta di sini berupa teks. FORM dan NOT_FOUND diisi lewat str.format(),
jadi CSS/JavaScript disisipkan sebagai *nilai* (bukan ditulis langsung di dalam
template) agar tanda kurung kurawal { } di dalamnya tidak dianggap placeholder.
"""

# CSS dan JavaScript dipisah dari FORM karena FORM.format() menganggap { }
# sebagai placeholder. Kurung kurawal di dalam *nilai* yang disisipkan
# (style=STYLE, script=SCRIPT, dan sebagainya) tidak diproses oleh .format().
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
    flex-wrap: wrap;
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
  .header-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .pill-btn {
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
  .pill-btn:hover { border-color: var(--primary); }
  .hint { margin: 0 0 1rem; color: var(--muted); font-size: 0.9rem; }
  .result {
    margin-top: 0.25rem;
    padding: 0.8rem 1rem;
    border: 1px solid var(--border);
    border-left-width: 4px;
    border-radius: 8px;
    word-break: break-all;
  }
  .result:empty { display: none; }
  .result p { margin: 0 0 0.35rem; font-weight: 600; }
  .result p:last-child { margin-bottom: 0; }
  .result a { color: var(--primary); }
  .result.success { border-left-color: var(--success); }
  .result.error { border-left-color: var(--danger); }
  .not-found { text-align: center; }
  .not-found-icon { font-size: 3rem; margin-bottom: 0.5rem; }
  .not-found h2 { margin: 0 0 0.75rem; }
  .not-found p { margin: 0 0 0.5rem; word-break: break-all; }
  .not-found code {
    padding: 0.1rem 0.4rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    font-weight: 600;
  }
  .not-found .hint { margin-bottom: 1.25rem; }
  .btn-link {
    display: inline-block;
    padding: 0.7rem 1.25rem;
    border: 1.5px solid var(--primary);
    border-radius: 8px;
    color: var(--primary);
    font-weight: 600;
    text-decoration: none;
    transition: background 0.2s, box-shadow 0.2s;
  }
  .btn-link:hover { background: var(--ring); }
  .btn-link:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px var(--ring);
  }
  .hidden-div { display: none; }
"""

# Terjemahan UI. Bahasa bawaan: Inggris ("en"). Pilihan pengguna disimpan di
# localStorage dan dipakai oleh beranda maupun halaman 404.
# Kunci "err.*" sesuai dengan kode error di ERRORS (lihat di bawah).
I18N_SCRIPT = """
  (() => {
    const KEY = "lang";
    const DEFAULT_LANG = "en";
    const LANGS = ["en", "id"];
    const LANG_LABELS = { en: "🌐 English", id: "🌐 Indonesia" };

    const DICT = {
      en: {
        "page.title": "Link Shortener",
        "lang.title": "Language: English (click to switch to Indonesian)",
        "theme.system": "🖥️ System",
        "theme.dark": "🌙 Dark",
        "theme.light": "☀️ Light",
        "theme.title": "Theme: {label} (click to change)",
        "form.long_url": "Long URL",
        "form.long_url_placeholder": "https://example.com/very/long/page",
        "form.short_placeholder": "example",
        "btn.generate": "Generate short link",
        "btn.generating": "Generating...",
        "copy.title": "Copy",
        "copy.copied": "Copied!",
        "copy.failed": "Failed to copy",
        "msg.generate_ok": "Short link created successfully.",
        "verify.heading": "Verify link",
        "verify.hint": "Paste a short link to see where it really goes before opening it.",
        "verify.label": "Short link",
        "verify.placeholder": "https://.../code or just the code",
        "btn.verify": "Check link",
        "btn.verifying": "Checking...",
        "verify.points_to": "This link points to:",
        "nf.page_title": "Link not found - Link Shortener",
        "nf.title": "Link not found",
        "nf.message": "I couldn't find:",
        "nf.hint": "Check the short link again, or create a new one.",
        "nf.back": "Back to home",
        "err.network": "Could not connect to the server.",
        "err.server": "A server error occurred.",
        "err.url_empty": "The URL must not be empty.",
        "err.url_too_long": "The URL is too long.",
        "err.url_bad_chars": "The URL must not contain spaces or control characters.",
        "err.url_invalid": "The URL is not valid.",
        "err.url_scheme": "The URL must start with http:// or https://",
        "err.url_unreachable": "The URL could not be reached (it must respond with 200 OK).",
        "err.request_too_large": "The request is too large.",
        "err.route_not_found": "Route not found.",
        "err.db_unavailable": "The database is temporarily unavailable. Please try again shortly.",
        "err.link_empty": "The short link must not be empty.",
        "err.link_invalid": "The short link format is not valid.",
        "err.link_foreign": "This link does not belong to this service.",
        "err.link_not_found": "Short link not found."
      },
      id: {
        "page.title": "Link Shortener",
        "lang.title": "Bahasa: Indonesia (klik untuk beralih ke bahasa Inggris)",
        "theme.system": "🖥️ Sistem",
        "theme.dark": "🌙 Gelap",
        "theme.light": "☀️ Terang",
        "theme.title": "Tema: {label} (klik untuk mengganti)",
        "form.long_url": "URL panjang",
        "form.long_url_placeholder": "https://contoh.com/halaman/panjang",
        "form.short_placeholder": "contoh",
        "btn.generate": "Generate tautan pendek",
        "btn.generating": "Memproses...",
        "copy.title": "Salin",
        "copy.copied": "Tersalin!",
        "copy.failed": "Gagal menyalin",
        "msg.generate_ok": "Berhasil membuat tautan pendek.",
        "verify.heading": "Verifikasi link",
        "verify.hint": "Tempel link pendek untuk melihat tujuan aslinya sebelum membukanya.",
        "verify.label": "Link pendek",
        "verify.placeholder": "https://.../kode atau kode saja",
        "btn.verify": "Cek link",
        "btn.verifying": "Memeriksa...",
        "verify.points_to": "Link ini mengarah ke:",
        "nf.page_title": "Link tidak ditemukan - Link Shortener",
        "nf.title": "Link tidak ditemukan",
        "nf.message": "Saya tidak menemukan:",
        "nf.hint": "Periksa kembali link pendeknya, atau buat yang baru.",
        "nf.back": "Kembali ke beranda",
        "err.network": "Tidak dapat terhubung ke server.",
        "err.server": "Terjadi kesalahan pada server.",
        "err.url_empty": "URL tidak boleh kosong.",
        "err.url_too_long": "URL terlalu panjang.",
        "err.url_bad_chars": "URL tidak boleh mengandung spasi atau karakter kontrol.",
        "err.url_invalid": "URL tidak valid.",
        "err.url_scheme": "URL harus diawali dengan http:// atau https://",
        "err.url_unreachable": "URL tidak dapat diakses (harus membalas 200 OK).",
        "err.request_too_large": "Permintaan terlalu besar.",
        "err.route_not_found": "Rute tidak ditemukan.",
        "err.db_unavailable": "Database sedang tidak tersedia. Coba lagi sebentar lagi.",
        "err.link_empty": "Link pendek tidak boleh kosong.",
        "err.link_invalid": "Format link pendek tidak valid.",
        "err.link_foreign": "Link ini bukan berasal dari layanan ini.",
        "err.link_not_found": "Link pendek tidak ditemukan."
      }
    };

    const getLang = () => {
      try {
        const saved = localStorage.getItem(KEY);
        if (LANGS.includes(saved)) return saved;
      } catch {}
      return DEFAULT_LANG;
    };

    let lang = getLang();

    // Ambil teks untuk kunci tertentu; cadangan: bahasa Inggris, lalu kuncinya sendiri.
    const t = (key, vars = {}) => {
      let text = DICT[lang][key] ?? DICT.en[key] ?? key;
      for (const [name, value] of Object.entries(vars)) {
        text = text.replaceAll(`{${name}}`, value);
      }
      return text;
    };

    const has = (key) => key in DICT.en;

    const ATTRS = [
      ["placeholder", "data-i18n-placeholder"],
      ["title", "data-i18n-title"],
      ["aria-label", "data-i18n-aria-label"]
    ];

    // Terapkan terjemahan ke semua elemen yang punya atribut data-i18n*.
    const apply = () => {
      document.documentElement.lang = lang;
      document.querySelectorAll("[data-i18n]").forEach((el) => {
        el.textContent = t(el.getAttribute("data-i18n"));
      });
      ATTRS.forEach(([attr, dataAttr]) => {
        document.querySelectorAll(`[${dataAttr}]`).forEach((el) => {
          el.setAttribute(attr, t(el.getAttribute(dataAttr)));
        });
      });
    };

    window.i18n = { t, has, apply, getLang: () => lang };

    document.addEventListener("DOMContentLoaded", () => {
      apply();

      const btn = document.getElementById("lang-toggle");
      if (!btn) return;

      const render = () => {
        btn.textContent = LANG_LABELS[lang];
        btn.title = t("lang.title");
      };

      btn.addEventListener("click", () => {
        lang = LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length];
        try { localStorage.setItem(KEY, lang); } catch {}
        apply();
        render();
        // Beri tahu skrip lain agar menampilkan ulang teks dinamisnya.
        document.dispatchEvent(new CustomEvent("langchange", { detail: lang }));
      });

      render();
    });
  })();
"""

THEME_SCRIPT = """
  (() => {
    const KEY = "theme";
    const MODES = ["system", "dark", "light"];
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
      if (!btn) return;

      const render = () => {
        const label = window.i18n.t(`theme.${mode}`);
        btn.textContent = label;
        btn.title = window.i18n.t("theme.title", { label });
      };

      btn.addEventListener("click", () => {
        mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
        applyMode(mode);
        try { localStorage.setItem(KEY, mode); } catch {}
        render();
      });

      document.addEventListener("langchange", render);
      render();
    });
  })();
"""

SCRIPT = """
  (() => {
    document.addEventListener("DOMContentLoaded", () => {
      const i18n = window.i18n;

      // Ganti kunci terjemahan sebuah elemen (agar ikut berubah saat bahasa diganti).
      const setLabel = (el, key) => {
        el.setAttribute("data-i18n", key);
        el.textContent = i18n.t(key);
      };

      // Pesan error dari server: terjemahkan lewat "code", cadangannya teks dari server.
      const errorFrom = (data) => {
        const key = `err.${data.code}`;
        if (data.code && i18n.has(key)) return { type: "error", key };
        if (data.error) return { type: "error", text: data.error };
        return { type: "error", key: "err.server" };
      };

      // --- Tombol salin nama pendek ---
      const shortInput = document.getElementById("shortname");
      const copyBtn = document.getElementById("copy-short");
      let copyTimer;

      const setCopyTitle = (key) => {
        copyBtn.setAttribute("data-i18n-title", key);
        copyBtn.title = i18n.t(key);
      };

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
        setCopyTitle(ok ? "copy.copied" : "copy.failed");

        clearTimeout(copyTimer);
        copyTimer = setTimeout(() => {
          copyBtn.classList.remove("copied");
          setCopyTitle("copy.title");
        }, 1500);
      });

      // --- Tombol generate tautan pendek ---
      const form = document.getElementById("shorten-form");
      const longInput = document.getElementById("longuri");
      const generateBtn = document.getElementById("generate-short");
      const generateLabel = generateBtn.querySelector(".btn-label");
      const message = document.getElementById("message");
      let currentMessage = null; // { type, key } atau { type, text }

      const renderMessage = () => {
        if (!currentMessage) {
          message.textContent = "";
          message.className = "message";
          return;
        }
        const { type, key, text } = currentMessage;
        message.textContent = key ? i18n.t(key) : text;
        message.className = `message ${type}`;
      };

      const showMessage = (msg = null) => {
        currentMessage = msg;
        renderMessage();
      };

      const generate = async () => {
        if (!longInput.reportValidity()) return;

        generateBtn.disabled = true;
        setLabel(generateLabel, "btn.generating");
        showMessage();

        try {
          const res = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ longuri: longInput.value.trim() })
          });
          const data = await res.json().catch(() => ({}));

          if (!res.ok) {
            shortInput.value = "";
            showMessage(errorFrom(data));
            return;
          }

          // Ketika berhasil, tampilkan tautan pendek lengkap (scheme dan host).
          shortInput.value = window.origin + "/" + data.shortname;
          showMessage({ type: "success", key: "msg.generate_ok" });
        } catch {
          shortInput.value = "";
          showMessage({ type: "error", key: "err.network" });
        } finally {
          generateBtn.disabled = false;
          setLabel(generateLabel, "btn.generate");
        }
      };

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

      // --- Verifikasi link: cari URL asli dari link pendek ---
      const verifyForm = document.getElementById("verify-form");
      const verifyInput = document.getElementById("shortlink");
      const verifyBtn = document.getElementById("verify-btn");
      const verifyLabel = verifyBtn.querySelector(".btn-label");
      const verifyResult = document.getElementById("verify-result");
      let currentResult = null; // { type, key | text, url? }

      const renderResult = () => {
        verifyResult.replaceChildren();
        if (!currentResult) {
          verifyResult.className = "result";
          return;
        }
        const { type, key, text, url } = currentResult;
        verifyResult.className = `result ${type}`;
        const p = document.createElement("p");
        p.textContent = key ? i18n.t(key) : text;
        verifyResult.append(p);
        if (url) {
          const a = document.createElement("a");
          a.href = url;
          a.textContent = url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          verifyResult.append(a);
        }
      };

      const showResult = (res = null) => {
        currentResult = res;
        renderResult();
      };

      const verify = async () => {
        if (!verifyInput.reportValidity()) return;

        verifyBtn.disabled = true;
        setLabel(verifyLabel, "btn.verifying");
        showResult();

        try {
          const res = await fetch("/verify", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ shortlink: verifyInput.value.trim() })
          });
          const data = await res.json().catch(() => ({}));

          if (!res.ok) {
            showResult(errorFrom(data));
            return;
          }
          showResult({ type: "success", key: "verify.points_to", url: data.longuri });
        } catch {
          showResult({ type: "error", key: "err.network" });
        } finally {
          verifyBtn.disabled = false;
          setLabel(verifyLabel, "btn.verify");
        }
      };

      verifyForm.addEventListener("submit", (e) => {
        e.preventDefault();
        verify();
      });

      // Saat bahasa diganti, tampilkan ulang pesan dan hasil yang sedang tampil.
      document.addEventListener("langchange", () => {
        renderMessage();
        renderResult();
      });
    });
  })();
"""

FORM = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="page.title">Link Shortener</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27><text y=%27.9em%27 font-size=%2790%27>🔗</text></svg>">
  <style>{style}</style>
  <script>{i18n_script}</script>
  <script>{theme_script}</script>
  <script>{script}</script>
</head>
<body>
  <main>
    <header>
      <h1>🔗 Link Shortener</h1>
      <div class="header-actions">
        <button type="button" id="lang-toggle" class="pill-btn">🌐 English</button>
        <button type="button" id="theme-toggle" class="pill-btn">🖥️ System</button>
      </div>
    </header>

    <form id="shorten-form" class="card">
      <label><span data-i18n="form.long_url">Long URL</span>
        <input type="url" name="longuri" id="longuri" placeholder="https://example.com/very/long/page" data-i18n-placeholder="form.long_url_placeholder" required>
      </label>
      <button type="button" name="generate" id="generate-short" class="btn-secondary">
        <span aria-hidden="true">🎲</span> <span class="btn-label" data-i18n="btn.generate">Generate short link</span>
      </button>
      <div class="input-group">
        <input type="text" name="shortname" id="shortname" placeholder="example" data-i18n-placeholder="form.short_placeholder" readonly>
        <button type="button" id="copy-short" class="icon-btn" title="Copy" aria-label="Copy" data-i18n-title="copy.title" data-i18n-aria-label="copy.title">
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

    <section class="card" id="verify-section">
      <h2 data-i18n="verify.heading">Verify link</h2>
      <p class="hint" data-i18n="verify.hint">Paste a short link to see where it really goes before opening it.</p>
      <form id="verify-form">
        <label><span data-i18n="verify.label">Short link</span>
          <input type="text" id="shortlink" placeholder="https://.../code or just the code" data-i18n-placeholder="verify.placeholder" autocomplete="off" spellcheck="false" required>
        </label>
        <button type="submit" id="verify-btn" class="btn-secondary">
          <span aria-hidden="true">🔍</span> <span class="btn-label" data-i18n="btn.verify">Check link</span>
        </button>
      </form>
      <div id="verify-result" class="result" role="status" aria-live="polite"></div>
    </section>
  </main>
</body>
</html>
"""

NOT_FOUND = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title data-i18n="nf.page_title">Link not found - Link Shortener</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27><text y=%27.9em%27 font-size=%2790%27>🔗</text></svg>">
  <style>{style}</style>
  <script>{i18n_script}</script>
  <script>{theme_script}</script>
</head>
<body>
  <main>
    <header>
      <h1>🔗 Link Shortener</h1>
      <div class="header-actions">
        <button type="button" id="lang-toggle" class="pill-btn">🌐 English</button>
        <button type="button" id="theme-toggle" class="pill-btn">🖥️ System</button>
      </div>
    </header>

    <section class="card not-found">
      <div class="not-found-icon" aria-hidden="true">🔍</div>
      <h2 data-i18n="nf.title">Link not found</h2>
      <p><span data-i18n="nf.message">I couldn't find:</span> <br /> <code>{link}</code></p>
      <p class="hint" data-i18n="nf.hint">Check the short link again, or create a new one.</p>
      <a class="btn-link" href="/" data-i18n="nf.back">Back to home</a>
    </section>
  </main>
</body>
</html>
"""
