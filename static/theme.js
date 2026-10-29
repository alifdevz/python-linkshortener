(() => {
  const KEY = 'theme';
  const MODES = ['system', 'dark', 'light'];
  const root = document.documentElement;

  const getMode = () => {
    try {
      const saved = localStorage.getItem(KEY);
      if (MODES.includes(saved)) return saved;
    } catch {}
    return 'system';
  };

  const applyMode = (mode) => {
    if (mode === 'system') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', mode);
    }
  };

  // Terapkan sedini mungkin supaya halaman tidak berkedip saat dimuat.
  let mode = getMode();
  applyMode(mode);

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;

    const render = () => {
      const label = window.i18n.t(`theme.${mode}`);
      btn.textContent = label;
      btn.title = window.i18n.t('theme.title', { label });
    };

    btn.addEventListener('click', () => {
      mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
      applyMode(mode);
      try {
        localStorage.setItem(KEY, mode);
      } catch {}
      render();
    });

    document.addEventListener('langchange', render);
    render();
  });
})();
