// ============================================================
// SIGDA — Sidebar Toggle & Persistence
// ============================================================
document.addEventListener('DOMContentLoaded', function () {

  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  const toggleBtns = document.querySelectorAll('[data-sidebar-toggle]');
  const STORAGE_KEY = 'sigda_sidebar_collapsed';

  if (!sidebar) return;

  // ── Desktop: restore collapsed state from localStorage ──
  function isDesktop() { return window.innerWidth >= 992; }
  function isMobile() { return window.innerWidth < 992; } // Mobile & Tablet

  if (isDesktop() && localStorage.getItem(STORAGE_KEY) === '1') {
    sidebar.classList.add('collapsed');
  }

  // ── Toggle button click ──
  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (isMobile()) {
        // Offcanvas mode
        sidebar.classList.toggle('show');
        if (backdrop) backdrop.classList.toggle('show', sidebar.classList.contains('show'));
        document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
      } else if (isDesktop()) {
        // Collapse/expand
        sidebar.classList.toggle('collapsed');
        localStorage.setItem(STORAGE_KEY, sidebar.classList.contains('collapsed') ? '1' : '0');
      }
      // Tablet: no toggle needed, hover handles it
    });
  });

  // ── Backdrop click closes mobile sidebar ──
  if (backdrop) {
    backdrop.addEventListener('click', function () {
      sidebar.classList.remove('show');
      backdrop.classList.remove('show');
      document.body.style.overflow = '';
    });
  }

  // ── Mobile: close sidebar when a link is clicked ──
  sidebar.querySelectorAll('a.sidebar-link').forEach(function (link) {
    link.addEventListener('click', function () {
      if (isMobile()) {
        sidebar.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // ── Auto-expand active collapsible section ──
  sidebar.querySelectorAll('.sidebar-submenu .sidebar-link.active').forEach(function (activeLink) {
    var collapseEl = activeLink.closest('.collapse');
    if (collapseEl) {
      var bsCollapse = new bootstrap.Collapse(collapseEl, { toggle: false });
      bsCollapse.show();
      // Also set the parent button as active
      var btn = sidebar.querySelector('[data-bs-target="#' + collapseEl.id + '"]');
      if (btn) {
        btn.classList.add('active');
        btn.setAttribute('aria-expanded', 'true');
      }
    }
  });

  // ── Handle resize: clean up mobile state ──
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      if (!isMobile()) {
        sidebar.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
        document.body.style.overflow = '';
      }
    }, 150);
  });

  // ── Desktop collapsed: Bootstrap tooltips on icons ──
  function refreshTooltips() {
    sidebar.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      var existing = bootstrap.Tooltip.getInstance(el);
      if (sidebar.classList.contains('collapsed') && isDesktop()) {
        if (!existing) new bootstrap.Tooltip(el, { placement: 'right', trigger: 'hover' });
      } else {
        if (existing) existing.dispose();
      }
    });
  }

  // Observe collapsed class
  var observer = new MutationObserver(function () { refreshTooltips(); });
  observer.observe(sidebar, { attributes: true, attributeFilter: ['class'] });
  refreshTooltips();
});
