/* ==========================================================================
   ФК «Барракуда» — интерактив без зависимостей
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  /* ---------- Мобильное меню ---------- */
  var burger = $("[data-burger]");
  var mobileNav = $("[data-mobile-nav]");
  if (burger && mobileNav) {
    burger.addEventListener("click", function () {
      var open = mobileNav.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    $$("a", mobileNav).forEach(function (a) {
      a.addEventListener("click", function () { mobileNav.classList.remove("open"); });
    });
  }

  /* ---------- Табы ---------- */
  $$("[data-tabs]").forEach(function (group) {
    var tabs = $$("[data-tab]", group);
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.getAttribute("data-tab");
        tabs.forEach(function (t) {
          var on = t === tab;
          t.classList.toggle("active", on);
          t.setAttribute("aria-selected", on ? "true" : "false");
        });
        $$("[data-panel]", group).forEach(function (panel) {
          panel.classList.toggle("active", panel.getAttribute("data-panel") === target);
        });
      });
    });
  });

  /* ---------- Фильтры карточек ---------- */
  $$("[data-filter-group]").forEach(function (wrap) {
    var buttons = $$("[data-filter]", wrap);
    var scopeSel = wrap.getAttribute("data-filter-scope");
    var scope = scopeSel ? $(scopeSel) : document;
    var items = $$("[data-cat]", scope);
    var counter = $("[data-filter-count]", wrap);

    function apply(value) {
      var shown = 0;
      items.forEach(function (item) {
        var cats = (item.getAttribute("data-cat") || "").split(/\s+/);
        var ok = value === "all" || cats.indexOf(value) !== -1;
        item.classList.toggle("is-hidden", !ok);
        if (ok) {
          shown++;
          item.classList.remove("visible");
          void item.offsetWidth;
          item.classList.add("visible");
        }
      });
      if (counter) counter.textContent = shown;
    }

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.classList.toggle("active", b === btn); });
        apply(btn.getAttribute("data-filter"));
      });
    });
  });

  /* ---------- Обратный отсчёт до матча ---------- */
  $$("[data-countdown]").forEach(function (root) {
    var iso = root.getAttribute("data-countdown");
    var target = new Date(iso).getTime();
    if (isNaN(target)) return;
    var cells = {
      d: $("[data-cd='d']", root),
      h: $("[data-cd='h']", root),
      m: $("[data-cd='m']", root),
      s: $("[data-cd='s']", root)
    };
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };

    function tick() {
      var diff = target - Date.now();
      if (diff < 0) diff = 0;
      var s = Math.floor(diff / 1000);
      var d = Math.floor(s / 86400);
      var h = Math.floor((s % 86400) / 3600);
      var m = Math.floor((s % 3600) / 60);
      var sec = s % 60;
      if (cells.d) cells.d.textContent = pad(d);
      if (cells.h) cells.h.textContent = pad(h);
      if (cells.m) cells.m.textContent = pad(m);
      if (cells.s) cells.s.textContent = pad(sec);
      if (diff === 0 && root.hasAttribute("data-countdown-live")) {
        root.setAttribute("data-countdown-done", "1");
      }
    }
    tick();
    setInterval(tick, 1000);
  });

  /* ---------- Бегущая строка: дублируем для бесшовности ---------- */
  $$("[data-ticker]").forEach(function (track) {
    if (track.getAttribute("data-ticker-ready") === "1") return;
    track.innerHTML = track.innerHTML + track.innerHTML;
    track.setAttribute("data-ticker-ready", "1");
  });

  /* ---------- Появление при скролле ---------- */
  var revealables = $$(".reveal");
  if ("IntersectionObserver" in window && revealables.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          var delay = parseInt(el.getAttribute("data-delay") || "0", 10);
          setTimeout(function () { el.classList.add("visible"); }, delay);
          io.unobserve(el);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add("visible"); });
  }

  /* ---------- Формы (демо без бэкенда) ---------- */
  $$("form[data-demo-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var note = $("[data-form-note]", form);
      var msg = form.getAttribute("data-success") || "Спасибо! Мы свяжемся с вами в ближайшее время.";
      if (note) {
        note.textContent = msg;
        note.style.color = "#6ee7b7";
      }
      form.reset();
    });
  });

  /* ---------- Год в подвале ---------- */
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---------- Тень шапки при скролле ---------- */
  var header = $(".site-header");
  if (header) {
    var onScroll = function () {
      header.style.boxShadow = window.scrollY > 12 ? "0 18px 40px -30px rgba(0,0,0,0.95)" : "none";
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }
})();
