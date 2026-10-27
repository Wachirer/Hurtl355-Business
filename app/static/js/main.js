/**
 * Hurtl355 — Public Page JavaScript
 * Covers: dark mode, custom cursor, smooth scroll, nav scroll spy,
 * portfolio filter, lightbox, video modal, audio player, pricing tabs,
 * review form, contact form, scroll reveal.
 */

/* ── 1. Dark Mode ─────────────────────────────────────────────────────────── */
(function initTheme() {
  const root    = document.documentElement;
  const toggle  = document.getElementById('themeToggle');
  const toggleF = document.getElementById('themeToggleFooter');
  const iconEl  = document.getElementById('themeIcon');
  const iconElF = document.getElementById('themeIconFooter');

  function getTheme() {
    return root.getAttribute('data-theme');
  }

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = theme === 'dark' ? '🌙' : '☀️';
    if (iconEl)  iconEl.textContent  = icon;
    if (iconElF) iconElF.textContent = icon;
  }

  // Set correct icon on load
  setTheme(getTheme());

  function toggleTheme() { setTheme(getTheme() === 'dark' ? 'light' : 'dark'); }
  toggle  && toggle.addEventListener('click', toggleTheme);
  toggleF && toggleF.addEventListener('click', toggleTheme);
})();


/* ── 2. Footer year ───────────────────────────────────────────────────────── */
const fyEl = document.getElementById('footerYear');
if (fyEl) fyEl.textContent = new Date().getFullYear();


/* ── 3. Custom Cursor (desktop) ───────────────────────────────────────────── */
(function initCursor() {
  const dot  = document.getElementById('cursorDot');
  const ring = document.getElementById('cursorRing');
  if (!dot || !ring) return;

  let mx = -200, my = -200;
  let rx = -200, ry = -200;
  let raf;

  window.addEventListener('mousemove', function(e) {
    mx = e.clientX; my = e.clientY;
    dot.style.left = mx + 'px';
    dot.style.top  = my + 'px';
  });

  // Smooth ring lag
  function animateRing() {
    rx += (mx - rx) * 0.14;
    ry += (my - ry) * 0.14;
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    raf = requestAnimationFrame(animateRing);
  }
  animateRing();

  // Expand ring on hoverable elements
  document.addEventListener('mouseover', function(e) {
    if (e.target.closest('a, button, .work-card, .service-card, .pricing-card')) {
      ring.classList.add('hovered');
    }
  });
  document.addEventListener('mouseout', function(e) {
    if (e.target.closest('a, button, .work-card, .service-card, .pricing-card')) {
      ring.classList.remove('hovered');
    }
  });
})();


/* ── 4. Sticky Nav ────────────────────────────────────────────────────────── */
(function initNav() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  let lastY = 0;
  window.addEventListener('scroll', function() {
    const y = window.scrollY;
    if (y > 80) {
      nav.style.boxShadow = '0 2px 24px rgba(0,0,0,0.15)';
    } else {
      nav.style.boxShadow = 'none';
    }
    lastY = y;
  }, { passive: true });
})();


/* ── 5. Mobile Hamburger ──────────────────────────────────────────────────── */
(function initHamburger() {
  const btn  = document.getElementById('hamburger');
  const menu = document.getElementById('mobileMenu');
  if (!btn || !menu) return;

  function open() {
    btn.classList.add('open');
    menu.classList.add('open');
    menu.removeAttribute('aria-hidden');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    btn.classList.remove('open');
    menu.classList.remove('open');
    menu.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  btn.addEventListener('click', function() {
    btn.classList.contains('open') ? close() : open();
  });

  // Close when a mobile link is clicked
  menu.querySelectorAll('.mobile-link').forEach(function(link) {
    link.addEventListener('click', close);
  });

  // Close on Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') close();
  });
})();


/* ── 6. Smooth Scroll ─────────────────────────────────────────────────────── */
document.querySelectorAll('.smooth-scroll').forEach(function(el) {
  el.addEventListener('click', function(e) {
    const href = el.getAttribute('href');
    if (!href || !href.startsWith('#')) return;
    const target = document.querySelector(href);
    if (!target) return;
    e.preventDefault();
    const navH = 64;
    const top  = target.getBoundingClientRect().top + window.scrollY - navH;
    window.scrollTo({ top: top, behavior: 'smooth' });
  });
});


/* ── 7. Pre-select service from pricing CTA ───────────────────────────────── */
document.querySelectorAll('[data-service]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    const service = btn.dataset.service || '';
    const sel = document.getElementById('ctxService');
    if (!sel) return;
    // Find closest matching option
    Array.from(sel.options).forEach(function(opt) {
      if (service.toLowerCase().includes(opt.value.toLowerCase().split(' ')[0]) ||
          opt.value.toLowerCase().includes(service.toLowerCase().split(' ')[0])) {
        sel.value = opt.value;
      }
    });
  });
});


/* ── 8. Scroll Reveal ─────────────────────────────────────────────────────── */
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  // Apply stagger delays
  els.forEach(function(el) {
    const delay = el.dataset.delay || 0;
    el.style.transitionDelay = delay + 'ms';
  });

  const obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  els.forEach(function(el) { obs.observe(el); });
})();


/* ── 9. Portfolio Filter ──────────────────────────────────────────────────── */
(function initPortfolioFilter() {
  const tabs   = document.querySelectorAll('.portfolio__tabs .tab-btn');
  const cards  = document.querySelectorAll('#worksGrid .work-card');
  const noRes  = document.getElementById('noResults');

  if (!tabs.length) return;

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');

      const filter = tab.dataset.tab;
      let visible  = 0;

      cards.forEach(function(card) {
        if (filter === 'all' || card.dataset.category === filter) {
          card.classList.remove('hidden');
          visible++;
        } else {
          card.classList.add('hidden');
        }
      });

      if (noRes) noRes.style.display = (visible === 0 ? 'block' : 'none');
    });
  });

  // Service card links → filter portfolio
  document.querySelectorAll('[data-filter]').forEach(function(link) {
    link.addEventListener('click', function(e) {
      const filter = link.dataset.filter;
      const matchTab = document.querySelector(`.portfolio__tabs [data-tab="${filter}"]`);
      if (matchTab) {
        setTimeout(function() { matchTab.click(); }, 300);
      }
    });
  });
})();


/* ── 10. Lightbox (graphic images) ───────────────────────────────────────── */
(function initLightbox() {
  const lb    = document.getElementById('lightbox');
  const img   = document.getElementById('lightboxImg');
  const close = document.getElementById('lightboxClose');
  if (!lb || !img) return;

  function open(src) {
    img.src = src;
    lb.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
  }
  function closeLb() {
    lb.setAttribute('hidden', '');
    document.body.style.overflow = '';
    img.src = '';
  }

  document.addEventListener('click', function(e) {
    const media = e.target.closest('.work-card__media--image');
    if (media) {
      const src = media.dataset.lightbox;
      if (src) open(src);
    }
  });

  close && close.addEventListener('click', closeLb);
  lb.addEventListener('click', function(e) { if (e.target === lb) closeLb(); });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeLb(); });
})();


/* ── 11. Video Modal ──────────────────────────────────────────────────────── */
(function initVideoModal() {
  const modal   = document.getElementById('videoModal');
  const vid     = document.getElementById('modalVideo');
  const iframe  = document.getElementById('modalIframe');
  const closBtn = document.getElementById('videoClose');
  if (!modal) return;

  function closeModal() {
    modal.setAttribute('hidden', '');
    document.body.style.overflow = '';
    if (vid)    { vid.pause();   vid.src = ''; vid.style.display = 'none'; }
    if (iframe) { iframe.src = ''; iframe.style.display = 'none'; }
  }

  function isEmbed(url) {
    return url && (url.includes('youtube') || url.includes('youtu.be') ||
                   url.includes('vimeo'));
  }

  function toEmbed(url) {
    if (url.includes('youtu.be/')) {
      const id = url.split('youtu.be/')[1].split('?')[0];
      return 'https://www.youtube.com/embed/' + id + '?autoplay=1';
    }
    if (url.includes('youtube.com/watch')) {
      const id = new URL(url).searchParams.get('v');
      return 'https://www.youtube.com/embed/' + id + '?autoplay=1';
    }
    if (url.includes('vimeo.com/')) {
      const id = url.split('vimeo.com/')[1].split('?')[0];
      return 'https://player.vimeo.com/video/' + id + '?autoplay=1';
    }
    return url;
  }

  document.addEventListener('click', function(e) {
    const media = e.target.closest('.work-card__media--video');
    if (!media) return;

    const src    = media.dataset.videoSrc;
    const extUrl = media.dataset.videoExt;

    modal.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';

    if (extUrl && isEmbed(extUrl)) {
      iframe.src = toEmbed(extUrl);
      iframe.style.display = 'block';
      vid.style.display = 'none';
    } else if (src) {
      const source = vid.querySelector('source');
      if (source) source.src = src;
      vid.load();
      vid.style.display = 'block';
      vid.play();
      iframe.style.display = 'none';
    }
  });

  closBtn && closBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', function(e) { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });
})();


/* ── 12. Music / Audio Player ─────────────────────────────────────────────── */
(function initAudioPlayers() {
  let activeAudio = null;
  let activeCard  = null;

  function formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  document.addEventListener('click', function(e) {
    const btn = e.target.closest('.music-play-btn');
    if (!btn) return;

    const card     = btn.closest('.work-card__music');
    const src      = btn.dataset.audio;
    const extUrl   = btn.dataset.ext;
    const icon     = btn.querySelector('.play-icon');
    const progress = card ? card.querySelector('.music-progress__fill') : null;
    const timeCur  = card ? card.querySelector('.time-current') : null;
    const timeTotal = card ? card.querySelector('.time-total') : null;

    // External links — open in new tab
    if (extUrl && !src) {
      window.open(extUrl, '_blank');
      return;
    }

    if (!src) return;

    // Same card → toggle
    if (activeCard === card && activeAudio) {
      if (activeAudio.paused) {
        activeAudio.play();
        if (icon) icon.textContent = '⏸';
      } else {
        activeAudio.pause();
        if (icon) icon.textContent = '▶';
      }
      return;
    }

    // Stop previous
    if (activeAudio) {
      activeAudio.pause();
      if (activeCard) {
        const prevIcon = activeCard.querySelector('.play-icon');
        if (prevIcon) prevIcon.textContent = '▶';
      }
    }

    // New audio
    const audio = new Audio(src);
    activeAudio = audio;
    activeCard  = card;

    if (icon) icon.textContent = '⏸';

    audio.addEventListener('loadedmetadata', function() {
      if (timeTotal) timeTotal.textContent = formatTime(audio.duration);
    });

    audio.addEventListener('timeupdate', function() {
      if (!audio.duration) return;
      const pct = (audio.currentTime / audio.duration) * 100;
      if (progress) progress.style.width = pct + '%';
      if (timeCur)  timeCur.textContent  = formatTime(audio.currentTime);
    });

    audio.addEventListener('ended', function() {
      if (icon) icon.textContent = '▶';
      if (progress) progress.style.width = '0';
      activeAudio = null;
      activeCard  = null;
    });

    audio.play().catch(function() {
      if (icon) icon.textContent = '▶';
    });

    // Seek on progress bar click
    if (progress && progress.parentElement) {
      progress.parentElement.addEventListener('click', function(ev) {
        if (!audio.duration) return;
        const rect = progress.parentElement.getBoundingClientRect();
        const ratio = (ev.clientX - rect.left) / rect.width;
        audio.currentTime = ratio * audio.duration;
      });
    }
  });
})();


/* ── 13. Pricing Tabs ─────────────────────────────────────────────────────── */
(function initPricingTabs() {
  const tabs   = document.querySelectorAll('.pricing__tabs .tab-btn');
  const panels = document.querySelectorAll('.pricing__panel');

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      const target = tab.dataset.pricingTab;
      tabs.forEach(function(t) { t.classList.remove('active'); });
      panels.forEach(function(p) { p.classList.remove('active'); });
      tab.classList.add('active');
      const panel = document.getElementById('pricing-' + target);
      if (panel) panel.classList.add('active');
    });
  });
})();


/* ── 14. Star Picker ──────────────────────────────────────────────────────── */
(function initStarPicker() {
  const picker   = document.querySelector('.star-picker');
  const hiddenIn = document.getElementById('revRating');
  if (!picker || !hiddenIn) return;

  const stars = picker.querySelectorAll('.star-pick');

  function setRating(val) {
    hiddenIn.value = val;
    stars.forEach(function(s, i) {
      s.classList.toggle('active', i < val);
    });
  }

  stars.forEach(function(star, i) {
    star.addEventListener('click', function() { setRating(i + 1); });
    star.addEventListener('mouseenter', function() {
      stars.forEach(function(s, j) { s.classList.toggle('active', j <= i); });
    });
  });

  picker.addEventListener('mouseleave', function() {
    const cur = parseInt(hiddenIn.value, 10) || 0;
    stars.forEach(function(s, i) { s.classList.toggle('active', i < cur); });
  });
})();


/* ── 15. Review Form ──────────────────────────────────────────────────────── */
(function initReviewForm() {
  const form     = document.getElementById('reviewForm');
  const feedback = document.getElementById('reviewFeedback');
  if (!form || !feedback) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    feedback.className = 'form-feedback';
    feedback.textContent = 'Sending…';

    const data = {
      name:    form.querySelector('[name=name]').value.trim(),
      role:    form.querySelector('[name=role]')?.value.trim() || '',
      rating:  parseInt(document.getElementById('revRating')?.value || '0', 10),
      message: form.querySelector('[name=message]').value.trim(),
      website: form.querySelector('[name=website]')?.value || '',
    };

    try {
      const res  = await fetch('/api/testimonials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const json = await res.json();

      if (res.ok && json.ok) {
        feedback.className = 'form-feedback success';
        feedback.textContent = json.message || 'Thank you! Your review is pending approval.';
        form.reset();
        document.querySelectorAll('.star-pick').forEach(function(s) {
          s.classList.remove('active');
        });
        if (document.getElementById('revRating')) document.getElementById('revRating').value = '0';
      } else {
        feedback.className = 'form-feedback error';
        feedback.textContent = json.error || 'Something went wrong. Please try again.';
      }
    } catch (err) {
      feedback.className = 'form-feedback error';
      feedback.textContent = 'Network error. Please try again.';
    }
  });
})();


/* ── 16. Contact Form ─────────────────────────────────────────────────────── */
(function initContactForm() {
  const form     = document.getElementById('contactForm');
  const feedback = document.getElementById('contactFeedback');
  if (!form || !feedback) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    feedback.className = 'form-feedback';
    feedback.textContent = 'Sending…';

    const data = {
      name:    form.querySelector('[name=name]').value.trim(),
      email:   form.querySelector('[name=email]').value.trim(),
      service: form.querySelector('[name=service]').value,
      message: form.querySelector('[name=message]').value.trim(),
      website: form.querySelector('[name=website]')?.value || '',
    };

    try {
      const res  = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const json = await res.json();

      if (res.ok && json.ok) {
        feedback.className = 'form-feedback success';
        feedback.textContent = json.message || 'Message sent! I\'ll be in touch shortly.';
        form.reset();
      } else {
        feedback.className = 'form-feedback error';
        feedback.textContent = json.error || 'Something went wrong. Please try again.';
      }
    } catch (err) {
      feedback.className = 'form-feedback error';
      feedback.textContent = 'Network error. Please try again.';
    }
  });
})();
