/* מינה — לוגיקת האתר: ניווט מובייל, רינדור תפריט, הדגשת סעיף פעיל, אנימציית כניסה */
(function () {
  'use strict';

  /* ---------- שנה בפוטר ---------- */
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- ניווט מובייל ---------- */
  var nav = document.getElementById('nav');
  var navToggle = document.getElementById('navToggle');

  if (nav && navToggle) {
    navToggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? 'סגירת תפריט ניווט' : 'פתיחת תפריט ניווט');
    });

    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.focus();
      }
    });
  }

  /* ---------- צל להדר בגלילה ---------- */
  var header = document.getElementById('siteHeader');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-stuck', window.scrollY > 8);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- רינדור התפריט מתוך menu-data.js ---------- */
  var tabsEl = document.getElementById('menuTabs');
  var panelsEl = document.getElementById('menuPanels');

  function itemHtml(item) {
    var note = item.note ? '<span class="note">' + item.note + '</span>' : '';
    var price = (item.price || item.price === 0) ? '<span class="price">' + item.price + ' ₪</span>' : '';
    return '<li class="menu-item">' +
             '<span class="name">' + item.name + note + '</span>' + price +
           '</li>';
  }

  function groupHtml(group) {
    return '<div class="menu-group">' +
             '<h3>' + group.title + '</h3>' +
             '<ul class="menu-list">' + (group.items || []).map(itemHtml).join('') + '</ul>' +
           '</div>';
  }

  function renderMenu() {
    if (!tabsEl || !panelsEl || typeof MENU === 'undefined') return;

    // מציגים רק קטגוריות שיש בהן תוכן, כדי שקטגוריות שטרם הוזנו לא יופיעו ריקות.
    var cats = MENU.filter(function (c) {
      return (c.groups || []).some(function (g) { return (g.items || []).length; });
    });
    if (!cats.length) return;

    tabsEl.innerHTML = cats.map(function (cat, i) {
      return '<button class="menu-tab" type="button" role="tab" id="tab-' + cat.id + '"' +
             ' aria-controls="panel-' + cat.id + '" aria-selected="' + (i === 0) + '"' +
             ' tabindex="' + (i === 0 ? '0' : '-1') + '">' + cat.title + '</button>';
    }).join('');

    panelsEl.innerHTML = cats.map(function (cat, i) {
      var groups = (cat.groups || []).filter(function (g) { return (g.items || []).length; });
      return '<div class="menu-panel" role="tabpanel" id="panel-' + cat.id + '"' +
             ' aria-labelledby="tab-' + cat.id + '"' + (i === 0 ? '' : ' hidden') + '>' +
               '<div class="menu-groups">' + groups.map(groupHtml).join('') + '</div>' +
             '</div>';
    }).join('');

    var tabs = Array.prototype.slice.call(tabsEl.querySelectorAll('.menu-tab'));

    function select(index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute('aria-selected', String(on));
        tab.tabIndex = on ? 0 : -1;
        document.getElementById(tab.getAttribute('aria-controls')).hidden = !on;
      });
      if (focus) tabs[index].focus();
    }

    tabsEl.addEventListener('click', function (e) {
      var tab = e.target.closest('.menu-tab');
      if (tab) select(tabs.indexOf(tab), false);
    });

    // ניווט מקלדת בין הלשוניות. RTL — חץ שמאל מתקדם, חץ ימין חוזר.
    tabsEl.addEventListener('keydown', function (e) {
      var current = tabs.indexOf(document.activeElement);
      if (current < 0) return;
      var next = null;
      if (e.key === 'ArrowLeft') next = (current + 1) % tabs.length;
      else if (e.key === 'ArrowRight') next = (current - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      if (next !== null) { e.preventDefault(); select(next, true); }
    });
  }

  renderMenu();

  /* ---------- הדגשת הסעיף הפעיל בניווט ---------- */
  var navLinks = nav ? Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]')) : [];
  var sections = navLinks
    .map(function (a) { return document.querySelector(a.getAttribute('href')); })
    .filter(Boolean);

  if (sections.length && 'IntersectionObserver' in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        navLinks.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach(function (s) { spy.observe(s); });
  }

  /* ---------- אנימציית כניסה בגלילה ---------- */
  var revealTargets = document.querySelectorAll('.section-head, .about-copy, .about-media, .review, .gallery-grid > *, .map-wrap, .menu-tabs');

  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var reveal = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px' });

    revealTargets.forEach(function (el) {
      el.classList.add('reveal');
      reveal.observe(el);
    });
  }
})();
