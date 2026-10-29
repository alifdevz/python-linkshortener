(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const i18n = window.i18n;

    // Ganti kunci terjemahan sebuah elemen (agar ikut berubah saat bahasa diganti).
    const setLabel = (el, key) => {
      el.setAttribute('data-i18n', key);
      el.textContent = i18n.t(key);
    };

    // Pesan error dari server: terjemahkan lewat "code", cadangannya teks dari server.
    const errorFrom = (data) => {
      const key = `err.${data.code}`;
      if (data.code && i18n.has(key)) return { type: 'error', key };
      if (data.error) return { type: 'error', text: data.error };
      return { type: 'error', key: 'err.server' };
    };

    // --- Tombol salin nama pendek ---
    const shortInput = document.getElementById('shortname');
    const copyBtn = document.getElementById('copy-short');
    let copyTimer;

    const setCopyTitle = (key) => {
      copyBtn.setAttribute('data-i18n-title', key);
      copyBtn.title = i18n.t(key);
    };

    const copyText = async (text) => {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        // Cadangan untuk konteks tidak aman (misalnya http:// lewat IP LAN).
        shortInput.select();
        try {
          return document.execCommand('copy');
        } catch {
          return false;
        }
      }
    };

    copyBtn.addEventListener('click', async () => {
      if (!shortInput.value) {
        shortInput.focus();
        return;
      }
      const ok = await copyText(shortInput.value);
      copyBtn.classList.toggle('copied', ok);
      setCopyTitle(ok ? 'copy.copied' : 'copy.failed');

      clearTimeout(copyTimer);
      copyTimer = setTimeout(() => {
        copyBtn.classList.remove('copied');
        setCopyTitle('copy.title');
      }, 1500);
    });

    // --- Tombol generate tautan pendek ---
    const form = document.getElementById('shorten-form');
    const longInput = document.getElementById('longuri');
    const generateBtn = document.getElementById('generate-short');
    const generateLabel = generateBtn.querySelector('.btn-label');
    const message = document.getElementById('message');
    let currentMessage = null; // { type, key } atau { type, text }

    const renderMessage = () => {
      if (!currentMessage) {
        message.textContent = '';
        message.className = 'message';
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
      setLabel(generateLabel, 'btn.generating');
      showMessage();

      try {
        const res = await fetch('/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ longuri: longInput.value.trim() }),
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          shortInput.value = '';
          showMessage(errorFrom(data));
          return;
        }

        // Ketika berhasil, tampilkan tautan pendek lengkap (scheme dan host).
        shortInput.value = window.origin + '/' + data.shortname;
        showMessage({ type: 'success', key: 'msg.generate_ok' });
      } catch {
        shortInput.value = '';
        showMessage({ type: 'error', key: 'err.network' });
      } finally {
        generateBtn.disabled = false;
        setLabel(generateLabel, 'btn.generate');
      }
    };

    generateBtn.addEventListener('click', generate);
    longInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        generate();
      }
    });
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      generate();
    });

    // --- Verifikasi link: cari URL asli dari link pendek ---
    const verifyForm = document.getElementById('verify-form');
    const verifyInput = document.getElementById('shortlink');
    const verifyBtn = document.getElementById('verify-btn');
    const verifyLabel = verifyBtn.querySelector('.btn-label');
    const verifyResult = document.getElementById('verify-result');
    let currentResult = null; // { type, key | text, url? }

    const renderResult = () => {
      verifyResult.replaceChildren();
      if (!currentResult) {
        verifyResult.className = 'result';
        return;
      }
      const { type, key, text, url } = currentResult;
      verifyResult.className = `result ${type}`;
      const p = document.createElement('p');
      p.textContent = key ? i18n.t(key) : text;
      verifyResult.append(p);
      if (url) {
        const a = document.createElement('a');
        a.href = url;
        a.textContent = url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
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
      setLabel(verifyLabel, 'btn.verifying');
      showResult();

      try {
        const res = await fetch('/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ shortlink: verifyInput.value.trim() }),
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          showResult(errorFrom(data));
          return;
        }
        showResult({
          type: 'success',
          key: 'verify.points_to',
          url: data.longuri,
        });
      } catch {
        showResult({ type: 'error', key: 'err.network' });
      } finally {
        verifyBtn.disabled = false;
        setLabel(verifyLabel, 'btn.verify');
      }
    };

    verifyForm.addEventListener('submit', (e) => {
      e.preventDefault();
      verify();
    });

    // Saat bahasa diganti, tampilkan ulang pesan dan hasil yang sedang tampil.
    document.addEventListener('langchange', () => {
      renderMessage();
      renderResult();
    });
  });
})();
