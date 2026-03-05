/**
 * Blue Falcon - Base JavaScript
 * Central JavaScript file for all pages
 * Contains theme toggle, common utilities, and initialization
 */

(function() {
    'use strict';

    // ============================================
    // Theme Toggle Functionality
    // ============================================
    const initThemeToggle = function() {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        const htmlElement = document.documentElement;
        
        if (!themeToggle || !themeIcon) return;
        
        // Check for saved theme preference or use system preference
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Apply saved theme or system preference
        if (savedTheme) {
            htmlElement.setAttribute('data-bs-theme', savedTheme);
            updateIcon(savedTheme);
        } else if (systemPrefersDark) {
            htmlElement.setAttribute('data-bs-theme', 'dark');
            updateIcon('dark');
        } else {
            htmlElement.setAttribute('data-bs-theme', 'light');
            updateIcon('light');
        }
        
        // Toggle theme on button click
        themeToggle.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateIcon(newTheme);
            
            // Dispatch custom event for other components to respond
            document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
        });
        
        function updateIcon(theme) {
            if (theme === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                htmlElement.setAttribute('data-bs-theme', newTheme);
                updateIcon(newTheme);
                
                // Dispatch custom event
                document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
            }
        });
    };

    // ============================================
    // Auto-dismiss Alerts
    // ============================================
    const initAutoDismissAlerts = function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        
        alerts.forEach(function(alert) {
            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    };

    // ============================================
    // Table Row Hover Effect
    // ============================================
    const initTableHover = function() {
        const tables = document.querySelectorAll('.table-hover');
        
        tables.forEach(function(table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(function(row) {
                row.style.cursor = 'pointer';
                row.addEventListener('click', function(e) {
                    // Only trigger if not clicking on a button or link
                    if (!e.target.closest('a') && !e.target.closest('button')) {
                        const link = row.dataset.href;
                        if (link) {
                            window.location.href = link;
                        }
                    }
                });
            });
        });
    };

    // ============================================
    // Form Validation Enhancement
    // ============================================
    const initFormValidation = function() {
        const forms = document.querySelectorAll('.needs-validation');
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    };

    // ============================================
    // Search Filter Debounce
    // ============================================
    const debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = function() {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // Make debounce available globally
    window.debounce = debounce;

    // ============================================
    // Initialize Search Filters
    // ============================================
    const initSearchFilters = function() {
        const searchInputs = document.querySelectorAll('[data-search-filter]');
        
        searchInputs.forEach(function(input) {
            const delay = input.dataset.searchDelay || 500;
            
            input.addEventListener('input', debounce(function() {
                const form = input.closest('form');
                if (form && form.dataset.autoSubmit === 'true') {
                    form.submit();
                }
            }, delay));
        });
    };

    // ============================================
    // Initialize Tooltips
    // ============================================
    const initTooltips = function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    };

    // ============================================
    // Initialize Popovers
    // ============================================
    const initPopovers = function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    };

    // ============================================
    // Confirmation Dialogs
    // ============================================
    const initConfirmDialogs = function() {
        document.addEventListener('click', function(e) {
            const trigger = e.target.closest('[data-confirm]');
            if (!trigger) return;
            
            const message = trigger.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    };

    // ============================================
    // AJAX CSRF Token Setup
    // ============================================
    const setupCSRFToken = function() {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrftoken) {
            window.csrfToken = csrftoken.value;
            
            // Setup AJAX to include CSRF token
            document.addEventListener('submit', function(e) {
                const form = e.target;
                if (form.method.toLowerCase() === 'ajax' || form.dataset.ajax === 'true') {
                    e.preventDefault();
                    
                    const formData = new FormData(form);
                    fetch(form.action, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': window.csrfToken
                        }
                    }).then(function(response) {
                        return response.json();
                    }).then(function(data) {
                        document.dispatchEvent(new CustomEvent('formSuccess', { 
                            detail: { form: form, data: data } 
                        }));
                    }).catch(function(error) {
                        document.dispatchEvent(new CustomEvent('formError', { 
                            detail: { form: form, error: error } 
                        }));
                    });
                }
            });
        }
    };

    // ============================================
    // Initialize on DOM Ready
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        initThemeToggle();
        initAutoDismissAlerts();
        initTableHover();
        initFormValidation();
        initSearchFilters();
        initTooltips();
        initPopovers();
        initConfirmDialogs();
        setupCSRFToken();
        
        // Dispatch ready event
        document.dispatchEvent(new Event('blueFalconReady'));
    });

    // ============================================
    // Accessibility Utilities
    // ============================================
    const prefersReducedMotion = function() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    };
    
    // Create ARIA live region for status messages
    const createLiveRegion = function() {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'aria-live-region';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'visually-hidden';
        document.body.appendChild(liveRegion);
        return liveRegion;
    };
    
    // Announce message to screen readers
    const announceToScreenReader = function(message) {
        let liveRegion = document.getElementById('aria-live-region');
        if (!liveRegion) {
            liveRegion = createLiveRegion();
        }
        liveRegion.textContent = message;
        // Clear after announcement
        setTimeout(function() {
            liveRegion.textContent = '';
        }, 1000);
    };
    
    // ============================================
    // Global Utilities
    // ============================================
    window.BlueFalcon = {
        // Refresh the page
        refresh: function() {
            window.location.reload();
        },
        
        // Redirect to URL
        redirect: function(url) {
            window.location.href = url;
        },
        
        // Show notification (using Bootstrap alerts) - WCAG 4.1.3 Status Messages
        notify: function(message, type) {
            type = type || 'info';
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-' + type + ' alert-dismissible';
            alertDiv.setAttribute('role', 'alert');
            alertDiv.setAttribute('aria-live', 'polite');
            alertDiv.setAttribute('aria-atomic', 'true');
            alertDiv.innerHTML = message + 
                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
            
            const container = document.querySelector('.container-fluid') || document.body;
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds (respect reduced motion preference)
            const dismissDelay = prefersReducedMotion() ? 10000 : 5000;
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }, dismissDelay);
            
            // Announce to screen readers
            announceToScreenReader(message);
        },
        
        // Get current theme
        getTheme: function() {
            return document.documentElement.getAttribute('data-bs-theme') || 'dark';
        },
        
        // Set theme programmatically
        setTheme: function(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            announceToScreenReader('Theme changed to ' + theme + ' mode');
        },
        
        // Accessibility utilities
        announce: announceToScreenReader,
        prefersReducedMotion: prefersReducedMotion
    };

})();
