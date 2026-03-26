/**
 * Blue Falcon Landing Page - Main JavaScript
 * Handles interactivity, animations, and dynamic features
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    Navigation.init();
    MobileMenu.init();
    SmoothScroll.init();
    AnimateOnScroll.init();
    CounterAnimation.init();
    ParallaxEffect.init();
    FormHandler.init();
});

/**
 * Navigation Module
 * Handles navbar scroll effects and active state
 */
const Navigation = {
    init() {
        this.navbar = document.getElementById('navbar');
        this.navLinks = document.querySelectorAll('.nav-link');
        
        this.bindEvents();
        this.checkScroll();
    },
    
    bindEvents() {
        window.addEventListener('scroll', () => this.checkScroll());
    },
    
    checkScroll() {
        const scrollPosition = window.scrollY;
        
        // Add scrolled class when page is scrolled
        if (scrollPosition > 50) {
            this.navbar?.classList.add('scrolled');
        } else {
            this.navbar?.classList.remove('scrolled');
        }
        
        // Update active nav link based on scroll position
        this.updateActiveNavLink(scrollPosition);
    },
    
    updateActiveNavLink(scrollPosition) {
        const sections = document.querySelectorAll('section[id]');
        const sectionOffset = 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - sectionOffset;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                this.navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }
};

/**
 * Mobile Menu Module
 * Handles mobile navigation toggle
 */
const MobileMenu = {
    init() {
        this.toggle = document.getElementById('mobileMenuToggle');
        this.menu = document.getElementById('navMenu');
        this.menuLinks = this.menu?.querySelectorAll('a');
        
        this.bindEvents();
    },
    
    bindEvents() {
        this.toggle?.addEventListener('click', () => this.toggleMenu());
        
        // Close menu when clicking a link
        this.menuLinks?.forEach(link => {
            link.addEventListener('click', () => this.closeMenu());
        });
        
        // Close menu on resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.closeMenu();
            }
        });
    },
    
    toggleMenu() {
        this.menu?.classList.toggle('active');
        this.toggle?.classList.toggle('active');
        
        // Toggle aria-expanded
        const isExpanded = this.menu?.classList.contains('active');
        this.toggle?.setAttribute('aria-expanded', isExpanded);
    },
    
    closeMenu() {
        this.menu?.classList.remove('active');
        this.toggle?.classList.remove('active');
        this.toggle?.setAttribute('aria-expanded', 'false');
    }
};

/**
 * Smooth Scroll Module
 * Handles smooth scrolling for anchor links
 */
const SmoothScroll = {
    init() {
        this.links = document.querySelectorAll('a[href^="#"]');
        this.bindEvents();
    },
    
    bindEvents() {
        this.links.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                
                // Skip if it's just "#" or external link
                if (href === '#' || href.length < 2) return;
                
                const target = document.querySelector(href);
                
                if (target) {
                    e.preventDefault();
                    this.scrollTo(target);
                }
            });
        });
    },
    
    scrollTo(target) {
        const offsetTop = target.offsetTop - 80; // Account for fixed navbar
        
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
};

/**
 * Animate On Scroll Module
 * Triggers animations when elements come into view
 */
const AnimateOnScroll = {
    init() {
        this.elements = document.querySelectorAll('.feature-card, .capability-card, .security-card, .testimonial-card, .tech-category');
        
        // Add animation class to elements
        this.elements.forEach(el => {
            el.classList.add('animate-on-scroll');
        });
        
        this.bindEvents();
        this.checkElements(); // Check on load
    },
    
    bindEvents() {
        window.addEventListener('scroll', () => this.checkElements());
    },
    
    checkElements() {
        const triggerBottom = window.innerHeight * 0.85;
        
        this.elements.forEach(el => {
            const elementTop = el.getBoundingClientRect().top;
            
            if (elementTop < triggerBottom) {
                el.classList.add('visible');
            }
        });
    }
};

/**
 * Counter Animation Module
 * Animates numbers counting up
 */
const CounterAnimation = {
    init() {
        this.counters = document.querySelectorAll('.stat-number[data-count]');
        this.animated = false;
        
        this.bindEvents();
        this.checkCounters(); // Check on load
    },
    
    bindEvents() {
        window.addEventListener('scroll', () => this.checkCounters());
    },
    
    checkCounters() {
        if (this.animated) return;
        
        const heroSection = document.getElementById('hero');
        if (!heroSection) return;
        
        const heroBottom = heroSection.getBoundingClientRect().bottom;
        const triggerPoint = window.innerHeight * 0.75;
        
        if (heroBottom > triggerPoint) {
            this.animated = true;
            this.animateAll();
        }
    },
    
    animateAll() {
        this.counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-count'));
            const duration = 2000; // 2 seconds
            const step = target / (duration / 16); // 60fps
            let current = 0;
            
            const updateCounter = () => {
                current += step;
                
                if (current < target) {
                    counter.textContent = Math.floor(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                }
            };
            
            updateCounter();
        });
    }
};

/**
 * Parallax Effect Module
 * Adds subtle parallax to floating elements
 */
const ParallaxEffect = {
    init() {
        this.floatingCards = document.querySelectorAll('.floating-card');
        
        if (this.floatingCards.length > 0) {
            this.bindEvents();
        }
    },
    
    bindEvents() {
        window.addEventListener('scroll', () => this.update());
    },
    
    update() {
        const scrollPosition = window.scrollY;
        const heroSection = document.getElementById('hero');
        
        if (!heroSection) return;
        
        const heroRect = heroSection.getBoundingClientRect();
        
        // Only apply parallax when hero is in view
        if (heroRect.bottom > 0 && heroRect.top < window.innerHeight) {
            this.floatingCards.forEach((card, index) => {
                const speed = 0.1 + (index * 0.05);
                const offset = scrollPosition * speed;
                card.style.transform = `translateY(${offset}px) rotate(${index * 2}deg)`;
            });
        }
    }
};

/**
 * Form Handler Module
 * Handles form submissions (for demo purposes)
 */
const FormHandler = {
    init() {
        this.forms = document.querySelectorAll('form');
        this.bindEvents();
    },
    
    bindEvents() {
        this.forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleSubmit(e, form));
        });
    },
    
    handleSubmit(e, form) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        // Show success message (demo)
        this.showNotification('Thank you! We\'ll be in touch soon.', 'success');
        
        // Reset form
        form.reset();
    },
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style notification
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '1rem 1.5rem',
            background: type === 'success' ? '#198754' : '#58a6ff',
            color: 'white',
            borderRadius: '0.5rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            zIndex: '1000',
            animation: 'slideIn 0.3s ease',
            maxWidth: '300px'
        });
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

/**
 * Chart Animation Module
 * Animates chart bars on scroll
 */
const ChartAnimation = {
    init() {
        this.chartBars = document.querySelectorAll('.chart-bars .bar');
        this.animated = false;
        
        if (this.chartBars.length > 0) {
            this.bindEvents();
            this.checkChart();
        }
    },
    
    bindEvents() {
        window.addEventListener('scroll', () => this.checkChart());
    },
    
    checkChart() {
        if (this.animated) return;
        
        const chart = document.querySelector('.chart-bars');
        if (!chart) return;
        
        const chartTop = chart.getBoundingClientRect().top;
        const triggerPoint = window.innerHeight * 0.75;
        
        if (chartTop < triggerPoint) {
            this.animated = true;
            this.animateBars();
        }
    },
    
    animateBars() {
        this.chartBars.forEach((bar, index) => {
            const targetHeight = bar.style.height;
            bar.style.height = '0%';
            
            setTimeout(() => {
                bar.style.transition = 'height 0.6s ease';
                bar.style.height = targetHeight;
            }, index * 100);
        });
    }
};

// Initialize chart animation
document.addEventListener('DOMContentLoaded', () => {
    ChartAnimation.init();
});

/**
 * Intersection Observer for lazy loading
 */
const LazyLoad = {
    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadElement(entry.target);
                    }
                });
            }, {
                rootMargin: '50px',
                threshold: 0.1
            });
            
            this.observeElements();
        }
    },
    
    observeElements() {
        const lazyElements = document.querySelectorAll('[data-lazy]');
        lazyElements.forEach(el => this.observer.observe(el));
    },
    
    loadElement(element) {
        const src = element.getAttribute('data-lazy');
        if (src) {
            if (element.tagName === 'IMG') {
                element.src = src;
            } else {
                element.style.backgroundImage = `url(${src})`;
            }
            element.removeAttribute('data-lazy');
        }
    }
};

// Initialize lazy loading
document.addEventListener('DOMContentLoaded', () => {
    LazyLoad.init();
});

/**
 * Tooltip Module
 * Shows tooltips on hover
 */
const Tooltip = {
    init() {
        this.tooltipElements = document.querySelectorAll('[data-tooltip]');
        this.bindEvents();
    },
    
    bindEvents() {
        this.tooltipElements.forEach(el => {
            el.addEventListener('mouseenter', (e) => this.show(e));
            el.addEventListener('mouseleave', () => this.hide());
        });
    },
    
    show(e) {
        const tooltipText = e.target.getAttribute('data-tooltip');
        
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tooltip';
        this.tooltip.textContent = tooltipText;
        
        Object.assign(this.tooltip.style, {
            position: 'absolute',
            padding: '0.5rem 0.75rem',
            background: 'rgba(15, 23, 42, 0.95)',
            color: 'white',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            zIndex: '700',
            pointerEvents: 'none',
            animation: 'fadeIn 0.2s ease'
        });
        
        document.body.appendChild(this.tooltip);
        this.updatePosition(e);
    },
    
    updatePosition(e) {
        const rect = e.target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        this.tooltip.style.top = `${rect.top - tooltipRect.height - 10}px`;
        this.tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltipRect.width / 2)}px`;
    },
    
    hide() {
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
    }
};

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
    Tooltip.init();
});

/**
 * Add CSS animations for notifications
 */
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

/**
 * Performance monitoring (development only)
 */
if (window.location.hostname === 'localhost') {
    window.addEventListener('load', () => {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        console.log(`Page Load Time: ${loadTime}ms`);
    });
}

/**
 * Console welcome message
 */
console.log('%c🦅 Blue Falcon', 'font-size: 24px; font-weight: bold; color: #58a6ff;');
console.log('%cAirport Operations Management System', 'font-size: 14px; color: #b0b0b0;');
console.log('%cBuilt with Django | Enterprise-Grade Security', 'font-size: 12px; color: #888888;');
