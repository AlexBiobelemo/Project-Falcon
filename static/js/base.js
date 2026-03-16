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

            // Save theme preference to user profile if authenticated
            saveThemePreference(newTheme);

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

    /**
     * Save theme preference to user profile via API
     */
    const saveThemePreference = function(theme) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        // Only save if user is authenticated (check for user menu or similar)
        const userMenu = document.querySelector('.user-avatar');
        if (!userMenu) return;

        fetch('/api/v1/user/preferences/', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            body: JSON.stringify({ theme_preference: theme })
        }).catch(err => console.log('Theme preference save failed:', err));
    };

    /**
     * Get cookie value by name
     */
    const getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
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
        }
    };

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

    // ============================================
    // Keyboard Shortcuts
    // ============================================
    const initKeyboardShortcuts = function() {
        // Track if user is typing in an input field
        const isInputFocused = function() {
            const activeElement = document.activeElement;
            return activeElement.tagName === 'INPUT' || 
                   activeElement.tagName === 'TEXTAREA' || 
                   activeElement.isContentEditable;
        };

        // Keyboard shortcut handler
        document.addEventListener('keydown', function(e) {
            // Don't trigger shortcuts when typing in inputs
            if (isInputFocused()) return;

            // Ctrl/Cmd + K - Global search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[name="search"], input[name="q"]');
                if (searchInput) {
                    searchInput.focus();
                    window.BlueFalcon.notify('Search focused', 'info');
                }
            }

            // Ctrl/Cmd + / - Show keyboard shortcuts help
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                showKeyboardShortcutsHelp();
            }

            // Ctrl/Cmd + R - Refresh page
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                window.BlueFalcon.notify('Refreshing page...', 'info');
                window.BlueFalcon.refresh();
            }

            // Ctrl/Cmd + D - Bookmark/Dashboard
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                const dashboardLink = document.querySelector('a[href="/"], a[href*="dashboard"]');
                if (dashboardLink) {
                    window.BlueFalcon.redirect(dashboardLink.href);
                }
            }

            // Ctrl/Cmd + N - New (context-aware)
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const newButton = document.querySelector('a[href*="create"], a[href*="new"]');
                if (newButton) {
                    newButton.click();
                }
            }

            // Ctrl/Cmd + E - Export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const exportButton = document.querySelector('a[href*="export"]');
                if (exportButton) {
                    exportButton.click();
                } else {
                    window.BlueFalcon.notify('No export option available', 'warning');
                }
            }

            // Escape - Close modals/alerts
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const bsModal = bootstrap.Modal.getInstance(openModal);
                    if (bsModal) bsModal.hide();
                }
                const alerts = document.querySelectorAll('.alert-dismissible');
                alerts.forEach(function(alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                });
            }

            // G then D - Go to Dashboard
            if (e.key === 'g') {
                const handleGKey = function(e2) {
                    if (e2.key === 'd') {
                        const dashboardLink = document.querySelector('a[href="/"], a[href*="dashboard"]');
                        if (dashboardLink) {
                            window.BlueFalcon.redirect(dashboardLink.href);
                        }
                    }
                    document.removeEventListener('keydown', handleGKey);
                };
                document.addEventListener('keydown', handleGKey);
                setTimeout(function() {
                    document.removeEventListener('keydown', handleGKey);
                }, 1000);
            }

            // G then A - Go to Analytics
            if (e.key === 'g') {
                const handleGKeyAnalytics = function(e2) {
                    if (e2.key === 'a') {
                        const analyticsLink = document.querySelector('a[href*="analytics"]');
                        if (analyticsLink) {
                            window.BlueFalcon.redirect(analyticsLink.href);
                        }
                    }
                    document.removeEventListener('keydown', handleGKeyAnalytics);
                };
                document.addEventListener('keydown', handleGKeyAnalytics);
                setTimeout(function() {
                    document.removeEventListener('keydown', handleGKeyAnalytics);
                }, 1000);
            }

            // ? - Show shortcuts help (when not in input)
            if (e.key === '?' && !isInputFocused()) {
                e.preventDefault();
                showKeyboardShortcutsHelp();
            }
        });
    };

    /**
     * Show keyboard shortcuts help modal
     */
    const showKeyboardShortcutsHelp = function() {
        let modal = document.getElementById('keyboardShortcutsModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
            bsModal.show();
            return;
        }

        modal = document.createElement('div');
        modal.id = 'keyboardShortcutsModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-keyboard"></i> Keyboard Shortcuts</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6 class="fw-bold mb-3">Navigation</h6>
                                <table class="table table-sm"><tbody>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>K</kbd></td><td>Focus search</td></tr>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>D</kbd></td><td>Go to Dashboard</td></tr>
                                    <tr><td><kbd>G</kbd> then <kbd>D</kbd></td><td>Go to Dashboard</td></tr>
                                    <tr><td><kbd>G</kbd> then <kbd>A</kbd></td><td>Go to Analytics</td></tr>
                                    <tr><td><kbd>Esc</kbd></td><td>Close modal/alert</td></tr>
                                </tbody></table>
                            </div>
                            <div class="col-md-6">
                                <h6 class="fw-bold mb-3">Actions</h6>
                                <table class="table table-sm"><tbody>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>R</kbd></td><td>Refresh page</td></tr>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>N</kbd></td><td>New/Create</td></tr>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>E</kbd></td><td>Export</td></tr>
                                    <tr><td><kbd>Ctrl</kbd>+<kbd>/</kbd></td><td>Show this help</td></tr>
                                    <tr><td><kbd>?</kbd></td><td>Show this help</td></tr>
                                </tbody></table>
                            </div>
                        </div>
                        <div class="alert alert-info mb-0 mt-3">
                            <i class="fas fa-info-circle"></i> Shortcuts disabled when typing in inputs.
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        window.BlueFalcon.announce('Keyboard shortcuts help opened');
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
        initKeyboardShortcuts();

        // Dispatch ready event
        document.dispatchEvent(new Event('blueFalconReady'));
    });

})();
