/**
 * Hurtl355 Admin Panel — JavaScript
 * Covers: sidebar, theme toggle, flash auto-dismiss.
 */

/* ── Theme Toggle ─────────────────────────────────────────────────────────── */
(function initAdminTheme() {
  const root = document.documentElement;
  const btn  = document.getElementById('adminThemeToggle');
  const icon = document.getElementById('adminThemeIcon');

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('adminTheme', theme);
    if (icon) icon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }

  // Sync icon on load
  setTheme(root.getAttribute('data-theme') || 'light');

  btn && btn.addEventListener('click', function() {
    const current = root.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  });
})();


/* ── Sidebar (mobile) ─────────────────────────────────────────────────────── */
(function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const open    = document.getElementById('adminHamburger');
  const close   = document.getElementById('sidebarClose');
  if (!sidebar) return;

  function openSidebar() {
    sidebar.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    document.body.style.overflow = '';
  }

  open  && open.addEventListener('click', openSidebar);
  close && close.addEventListener('click', closeSidebar);

  // Close when clicking a nav link on mobile
  sidebar.querySelectorAll('.sidebar__link').forEach(function(link) {
    link.addEventListener('click', function() {
      if (window.innerWidth <= 900) closeSidebar();
    });
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeSidebar();
  });
})();


/* ── Flash auto-dismiss after 5s ──────────────────────────────────────────── */
(function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(function() { el.remove(); }, 450);
    }, 5000);
  });
})();


/* ── Confirm delete (extra safety) ───────────────────────────────────────── */
document.querySelectorAll('form[data-confirm]').forEach(function(form) {
  form.addEventListener('submit', function(e) {
    if (!confirm(form.dataset.confirm || 'Are you sure?')) e.preventDefault();
  });
});
