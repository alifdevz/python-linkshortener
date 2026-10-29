// Terjemahan UI. Bahasa bawaan: Inggris ("en"). Pilihan pengguna disimpan di
// localStorage dan dipakai oleh beranda maupun halaman 404.
// Kunci "err.*" harus sesuai dengan kode error di ERRORS (link_shortener.py).
(() => {
  const KEY = 'lang';
  const DEFAULT_LANG = 'en';
  const LANGS = ['en', 'id'];
  const LANG_LABELS = { en: '🌐 English', id: '🌐 Indonesia' };

  const DICT = {
    en: {
      'page.title': 'Link Shortener',
      'lang.title': 'Language: English (click to switch to Indonesian)',
      'theme.system': '🖥️ System',
      'theme.dark': '🌙 Dark',
      'theme.light': '☀️ Light',
      'theme.title': 'Theme: {label} (click to change)',
      'form.long_url': 'Long URL',
      'form.long_url_placeholder': 'https://example.com/very/long/page',
      'form.short_placeholder': 'example',
      'btn.generate': 'Generate short link',
      'btn.generating': 'Generating...',
      'copy.title': 'Copy',
      'copy.copied': 'Copied!',
      'copy.failed': 'Failed to copy',
      'msg.generate_ok': 'Short link created successfully.',
      'verify.heading': 'Verify link',
      'verify.hint':
        'Paste a short link to see where it really goes before opening it.',
      'verify.label': 'Short link',
      'verify.placeholder': 'https://.../code or just the code',
      'btn.verify': 'Check link',
      'btn.verifying': 'Checking...',
      'verify.points_to': 'This link points to:',
      'nf.page_title': 'Link not found - Link Shortener',
      'nf.title': 'Link not found',
      'nf.message': "I couldn't find:",
      'nf.hint': 'Check the short link again, or create a new one.',
      'nf.back': 'Back to home',
      'err.network': 'Could not connect to the server.',
      'err.server': 'A server error occurred.',
      'err.url_empty': 'The URL must not be empty.',
      'err.url_too_long': 'The URL is too long.',
      'err.url_bad_chars':
        'The URL must not contain spaces or control characters.',
      'err.url_invalid': 'The URL is not valid.',
      'err.url_scheme': 'The URL must start with http:// or https://',
      'err.url_unreachable':
        'The URL could not be reached (it must respond with 200 OK).',
      'err.request_too_large': 'The request is too large.',
      'err.route_not_found': 'Route not found.',
      'err.db_unavailable':
        'The database is temporarily unavailable. Please try again shortly.',
      'err.link_empty': 'The short link must not be empty.',
      'err.link_invalid': 'The short link format is not valid.',
      'err.link_foreign': 'This link does not belong to this service.',
      'err.link_not_found': 'Short link not found.',
    },
    id: {
      'page.title': 'Link Shortener',
      'lang.title': 'Bahasa: Indonesia (klik untuk beralih ke bahasa Inggris)',
      'theme.system': '🖥️ Sistem',
      'theme.dark': '🌙 Gelap',
      'theme.light': '☀️ Terang',
      'theme.title': 'Tema: {label} (klik untuk mengganti)',
      'form.long_url': 'URL panjang',
      'form.long_url_placeholder': 'https://contoh.com/halaman/panjang',
      'form.short_placeholder': 'contoh',
      'btn.generate': 'Generate tautan pendek',
      'btn.generating': 'Memproses...',
      'copy.title': 'Salin',
      'copy.copied': 'Tersalin!',
      'copy.failed': 'Gagal menyalin',
      'msg.generate_ok': 'Berhasil membuat tautan pendek.',
      'verify.heading': 'Verifikasi link',
      'verify.hint':
        'Tempel link pendek untuk melihat tujuan aslinya sebelum membukanya.',
      'verify.label': 'Link pendek',
      'verify.placeholder': 'https://.../kode atau kode saja',
      'btn.verify': 'Cek link',
      'btn.verifying': 'Memeriksa...',
      'verify.points_to': 'Link ini mengarah ke:',
      'nf.page_title': 'Link tidak ditemukan - Link Shortener',
      'nf.title': 'Link tidak ditemukan',
      'nf.message': 'Saya tidak menemukan:',
      'nf.hint': 'Periksa kembali link pendeknya, atau buat yang baru.',
      'nf.back': 'Kembali ke beranda',
      'err.network': 'Tidak dapat terhubung ke server.',
      'err.server': 'Terjadi kesalahan pada server.',
      'err.url_empty': 'URL tidak boleh kosong.',
      'err.url_too_long': 'URL terlalu panjang.',
      'err.url_bad_chars':
        'URL tidak boleh mengandung spasi atau karakter kontrol.',
      'err.url_invalid': 'URL tidak valid.',
      'err.url_scheme': 'URL harus diawali dengan http:// atau https://',
      'err.url_unreachable': 'URL tidak dapat diakses (harus membalas 200 OK).',
      'err.request_too_large': 'Permintaan terlalu besar.',
      'err.route_not_found': 'Rute tidak ditemukan.',
      'err.db_unavailable':
        'Database sedang tidak tersedia. Coba lagi sebentar lagi.',
      'err.link_empty': 'Link pendek tidak boleh kosong.',
      'err.link_invalid': 'Format link pendek tidak valid.',
      'err.link_foreign': 'Link ini bukan berasal dari layanan ini.',
      'err.link_not_found': 'Link pendek tidak ditemukan.',
    },
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
    ['placeholder', 'data-i18n-placeholder'],
    ['title', 'data-i18n-title'],
    ['aria-label', 'data-i18n-aria-label'],
  ];

  // Terapkan terjemahan ke semua elemen yang punya atribut data-i18n*.
  const apply = () => {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    ATTRS.forEach(([attr, dataAttr]) => {
      document.querySelectorAll(`[${dataAttr}]`).forEach((el) => {
        el.setAttribute(attr, t(el.getAttribute(dataAttr)));
      });
    });
  };

  window.i18n = { t, has, apply, getLang: () => lang };

  document.addEventListener('DOMContentLoaded', () => {
    apply();

    const btn = document.getElementById('lang-toggle');
    if (!btn) return;

    const render = () => {
      btn.textContent = LANG_LABELS[lang];
      btn.title = t('lang.title');
    };

    btn.addEventListener('click', () => {
      lang = LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length];
      try {
        localStorage.setItem(KEY, lang);
      } catch {}
      apply();
      render();
      // Beri tahu skrip lain agar menampilkan ulang teks dinamisnya.
      document.dispatchEvent(new CustomEvent('langchange', { detail: lang }));
    });

    render();
  });
})();
