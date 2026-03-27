/**
 * Blue Falcon - Portfolio Landing Page
 */

(function () {
  "use strict";

  const CONFIG = {
    prefersReducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    isLowEnd:
      typeof navigator !== "undefined" &&
      ((navigator.deviceMemory && navigator.deviceMemory <= 4) ||
        (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4)),
    tiltStrength: 8,
    scrollThreshold: 50,
    animationStagger: 100,
  };

  const prefersReduced = CONFIG.prefersReducedMotion || CONFIG.isLowEnd;

  const clamp = (num, min, max) => Math.min(Math.max(num, min), max);
  const lerp = (start, end, t) => start + (end - start) * t;

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  function initNavbar() {
    const navbar = document.querySelector(".navbar");
    if (!navbar) return;

    const updateNavbar = () => {
      const scrolled = window.scrollY > CONFIG.scrollThreshold;
      navbar.setAttribute("data-elevate", scrolled ? "1" : "0");
    };

    window.addEventListener("scroll", throttle(updateNavbar, 100), { passive: true });
    updateNavbar();
  }

  function initMobileNav() {
    const toggle = document.querySelector(".nav-toggle");
    const menu = document.querySelector(".nav-menu");
    const actions = document.querySelector(".nav-actions");

    if (!toggle || !menu) return;

    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", !expanded);
      menu.classList.toggle("active");
      actions?.classList.toggle("active");
    });

    // Close menu on link click
    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        toggle.setAttribute("aria-expanded", "false");
        menu.classList.remove("active");
        actions?.classList.remove("active");
      });
    });

    // Close menu when clicking outside
    document.addEventListener("click", (e) => {
      if (
        menu.classList.contains("active") &&
        !menu.contains(e.target) &&
        !toggle.contains(e.target) &&
        (!actions || !actions.contains(e.target))
      ) {
        toggle.setAttribute("aria-expanded", "false");
        menu.classList.remove("active");
        actions?.classList.remove("active");
      }
    });
  }

  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", function (e) {
        const href = this.getAttribute("href");
        if (href === "#") return;

        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const offsetTop = target.offsetTop - 80;
          window.scrollTo({
            top: offsetTop,
            behavior: prefersReduced ? "auto" : "smooth",
          });
        }
      });
    });
  }

  function initTilt() {
    if (prefersReduced) return;

    const cards = document.querySelectorAll(".tilt-card, [data-tilt]");

    cards.forEach((card) => {
      let rafId = null;

      const handleMouseMove = (e) => {
        if (rafId) return;

        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * -CONFIG.tiltStrength;
        const rotateY = ((x - centerX) / centerX) * CONFIG.tiltStrength;

        // Set glow position for cards with ::before glow effect
        card.style.setProperty("--mx", `${(x / rect.width) * 100}%`);
        card.style.setProperty("--my", `${(y / rect.height) * 100}%`);

        rafId = requestAnimationFrame(() => {
          card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-4px)`;
          rafId = null;
        });
      };

      const handleMouseLeave = () => {
        if (rafId) cancelAnimationFrame(rafId);
        card.style.transform = "";
        card.style.setProperty("--mx", "50%");
        card.style.setProperty("--my", "0%");
      };

      card.addEventListener("mousemove", handleMouseMove);
      card.addEventListener("mouseleave", handleMouseLeave);
    });
  }

  function initCounters() {
    // Select both old stat-value and new stat-card-value elements
    const counters = document.querySelectorAll(".stat-value[data-count], .stat-card-value[data-count]");
    if (!counters.length) return;

    const animateCounter = (counter) => {
      const target = parseFloat(counter.getAttribute("data-count"));
      const duration = 2000;
      const startTime = performance.now();
      const suffix = counter.nextElementSibling?.classList.contains("stat-suffix") || 
                     counter.nextElementSibling?.classList.contains("stat-card-suffix")
        ? counter.nextElementSibling.textContent
        : "";

      const updateCounter = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (ease-out-quart)
        const eased = 1 - Math.pow(1 - progress, 4);
        const current = target * eased;

        if (target % 1 === 0) {
          counter.textContent = Math.floor(current).toLocaleString();
        } else {
          counter.textContent = current.toFixed(1);
        }

        if (progress < 1) {
          requestAnimationFrame(updateCounter);
        } else {
          counter.textContent = target.toLocaleString();
        }
      };

      requestAnimationFrame(updateCounter);
    };

    // Use Intersection Observer to trigger animation when visible
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              animateCounter(entry.target);
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.1 }
      );

      counters.forEach((counter) => observer.observe(counter));
    } else {
      counters.forEach(animateCounter);
    }
  }

  function initParticles() {
    const container = document.getElementById("particles");
    if (!container || prefersReduced) return;

    const particleCount = 30;

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement("div");
      particle.className = "particle";

      const size = Math.random() * 4 + 2;
      const left = Math.random() * 100;
      const delay = Math.random() * 20;
      const duration = Math.random() * 20 + 15;

      particle.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        left: ${left}%;
        bottom: -10px;
        animation-delay: ${delay}s;
        animation-duration: ${duration}s;
      `;

      container.appendChild(particle);
    }
  }

  function initLatencyDisplay() {
    const latencyEl = document.getElementById("latencyDisplay");
    if (!latencyEl) return;

    const updateLatency = () => {
      const baseLatency = 18;
      const variance = Math.floor(Math.random() * 12) - 6;
      const latency = baseLatency + variance;
      latencyEl.textContent = latency;
    };

    updateLatency();
    setInterval(updateLatency, 2000);
  }

  function initScrollReveal() {
    if (prefersReduced) return;

    const revealElements = document.querySelectorAll(
      ".section-header, .about-card, .feature-card, .stack-item, .library-card, .module-item"
    );

    revealElements.forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(30px)";
      el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              entry.target.style.opacity = "1";
              entry.target.style.transform = "translateY(0)";
            }, entry.target.dataset.delay || 0);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    revealElements.forEach((el, index) => {
      el.dataset.delay = (index % 5) * CONFIG.animationStagger;
      observer.observe(el);
    });
  }

  function initActiveNav() {
    const sections = document.querySelectorAll("section[id]");
    const navLinks = document.querySelectorAll(".nav-menu a");

    if (!sections.length || !navLinks.length) return;

    const updateActiveNav = throttle(() => {
      const scrollPos = window.scrollY + 150;

      sections.forEach((section) => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute("id");

        if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
          navLinks.forEach((link) => {
            link.classList.remove("active");
            if (link.getAttribute("href") === `#${sectionId}`) {
              link.classList.add("active");
            }
          });
        }
      });
    }, 100);

    window.addEventListener("scroll", updateActiveNav, { passive: true });
    updateActiveNav();
  }

  // ==========================================================================
  // Hero Dashboard Animation
  // ==========================================================================

  function initHeroAnimation() {
    if (prefersReduced) return;

    const mockupStats = document.querySelectorAll(".mockup-stat-card");
    const mockupRows = document.querySelectorAll(".mockup-table-row");

    // Animate stat cards
    mockupStats.forEach((card, index) => {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
      card.style.transition = `opacity 0.4s ease ${0.8 + index * 0.1}s, transform 0.4s ease ${0.8 + index * 0.1}s`;

      setTimeout(() => {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      }, 100);
    });

    // Animate table rows
    mockupRows.forEach((row, index) => {
      row.style.opacity = "0";
      row.style.transform = "translateX(-20px)";
      row.style.transition = `opacity 0.3s ease ${1.2 + index * 0.15}s, transform 0.3s ease ${1.2 + index * 0.15}s`;

      setTimeout(() => {
        row.style.opacity = "1";
        row.style.transform = "translateX(0)";
      }, 100);
    });
  }

  function initKeyboardNav() {
    document.addEventListener("keydown", (e) => {
      // Close mobile menu on Escape
      if (e.key === "Escape") {
        const toggle = document.querySelector(".nav-toggle");
        const menu = document.querySelector(".nav-menu");
        const actions = document.querySelector(".nav-actions");

        if (toggle && menu && toggle.getAttribute("aria-expanded") === "true") {
          toggle.setAttribute("aria-expanded", "false");
          menu.classList.remove("active");
          actions?.classList.remove("active");
        }
      }
    });
  }

  function optimizePerformance() {
    // Add passive listeners where possible
    const scrollElements = document.querySelectorAll(".section");
    
    scrollElements.forEach((el) => {
      el.style.contentVisibility = "auto";
      el.style.containIntrinsicSize = "800px";
    });

    // Lazy load images if any
    const images = document.querySelectorAll("img[loading='lazy']");
    if ("loading" in HTMLImageElement.prototype) {
      images.forEach((img) => {
        img.src = img.dataset.src || img.src;
      });
    }
  }

  function init() {
    // Wait for DOM to be ready
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
      return;
    }

    // Initialize all features
    initNavbar();
    initMobileNav();
    initSmoothScroll();
    initTilt();
    initCounters();
    initParticles();
    initLatencyDisplay();
    initScrollReveal();
    initActiveNav();
    initHeroAnimation();
    initKeyboardNav();
    optimizePerformance();
  }

  init();
})();
