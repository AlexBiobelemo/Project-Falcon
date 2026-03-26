/**
 * Blue Falcon - Real-time Notifications
 * WebSocket-based notification system with browser push notifications
 * 
 * Features:
 * - WebSocket connection for real-time updates
 * - Browser push notifications for flight status changes
 * - Notification preferences stored in localStorage
 * - WCAG 2.1 compliant notifications
 */

(function() {
    'use strict';

    // ============================================
    // Notification Manager Class
    // ============================================
    class NotificationManager {
        constructor() {
            this.ws = null;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 5;
            this.reconnectDelay = 3000;
            this.notificationsEnabled = false;
            this.notificationPreferences = {
                flight_status: true,
                flight_delay: true,
                flight_cancellation: true,
                gate_change: true,
                sound: false,
                desktop: true
            };
            this.soundEnabled = false;
            this.audioContext = null;
        }

        /**
         * Initialize the notification system
         */
        init() {
            this.loadPreferences();
            this.connect();
            this.initEventListeners();
            this.maybeShowPermissionPrompt();
            console.log('[Notifications] Notification system initialized');
        }

        /**
         * Load notification preferences from localStorage
         */
        loadPreferences() {
            const saved = localStorage.getItem('notification_preferences');
            if (saved) {
                try {
                    this.notificationPreferences = {
                        ...this.notificationPreferences,
                        ...JSON.parse(saved)
                    };
                } catch (e) {
                    console.error('[Notifications] Failed to load preferences:', e);
                }
            }
            this.notificationsEnabled = this.notificationPreferences.desktop;
        }

        /**
         * Save notification preferences to localStorage
         */
        savePreferences() {
            localStorage.setItem('notification_preferences', JSON.stringify(this.notificationPreferences));
        }

        /**
         * Request browser notification permission
         */
        async requestNotificationPermission() {
            if (!('Notification' in window)) {
                console.warn('[Notifications] Browser does not support notifications');
                return;
            }

            if (Notification.permission === 'granted') {
                this.notificationsEnabled = true;
                return;
            }

            if (Notification.permission !== 'denied') {
                try {
                    const permission = await Notification.requestPermission();
                    this.notificationsEnabled = permission === 'granted';
                    // Persist preference so we don't keep prompting.
                    this.notificationPreferences.desktop = this.notificationsEnabled;
                    this.savePreferences();
                } catch (e) {
                    console.error('[Notifications] Permission request failed:', e);
                }
            }
        }

        /**
         * Show a lightweight UI prompt that the user can click to enable notifications.
         * Browsers require Notification.requestPermission() to be triggered by a user gesture.
         */
        maybeShowPermissionPrompt() {
            if (!('Notification' in window)) return;
            if (!this.notificationPreferences.desktop) return;
            if (Notification.permission !== 'default') return;

            // Avoid duplicate prompts.
            if (document.getElementById('falcon-notification-permission')) return;

            const wrap = document.createElement('div');
            wrap.id = 'falcon-notification-permission';
            wrap.style.cssText = [
                'position:fixed',
                'right:16px',
                'bottom:16px',
                'z-index:9999',
                'max-width:360px',
                'padding:12px 12px 10px',
                'border-radius:12px',
                'background:#0b1220',
                'color:#e7eefc',
                'box-shadow:0 12px 36px rgba(0,0,0,.35)',
                'border:1px solid rgba(255,255,255,.08)',
                'font:14px/1.35 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif',
            ].join(';');

            wrap.innerHTML = `
                <div style="font-weight:650; margin-bottom:6px;">Enable desktop alerts?</div>
                <div style="opacity:.85; margin-bottom:10px;">Get flight status and gate-change notifications while you work.</div>
                <div style="display:flex; gap:8px; justify-content:flex-end;">
                    <button type="button" data-action="dismiss" style="padding:8px 10px; border-radius:10px; border:1px solid rgba(255,255,255,.16); background:transparent; color:inherit; cursor:pointer;">Not now</button>
                    <button type="button" data-action="enable" style="padding:8px 10px; border-radius:10px; border:1px solid rgba(255,255,255,.16); background:#1d4ed8; color:#fff; cursor:pointer;">Enable</button>
                </div>
            `;

            wrap.addEventListener('click', async (e) => {
                const btn = e.target && e.target.closest ? e.target.closest('button[data-action]') : null;
                if (!btn) return;

                const action = btn.getAttribute('data-action');
                if (action === 'dismiss') {
                    // Do not disable permanently; just hide the prompt for this session.
                    wrap.remove();
                    return;
                }

                if (action === 'enable') {
                    // User gesture happens here -> safe to call requestPermission().
                    await this.requestNotificationPermission();
                    wrap.remove();
                }
            });

            document.body.appendChild(wrap);
        }

        /**
         * Connect to WebSocket notification endpoint
         */
        connect() {
            // Check if WebSocket is available
            if (!('WebSocket' in window)) {
                console.warn('[Notifications] WebSocket not supported in this browser');
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[Notifications] Connected to notification service');
                    this.reconnectAttempts = 0;
                    // Request notification permission after connection
                    this.ws.send(JSON.stringify({
                        action: 'request_notification_permission'
                    }));
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(JSON.parse(event.data));
                };

                this.ws.onclose = () => {
                    console.log('[Notifications] Disconnected from notification service');
                    // Only reconnect if we had connected before
                    if (this.reconnectAttempts > 0 || this.ws.readyState === WebSocket.OPEN) {
                        this.scheduleReconnect();
                    }
                };

                this.ws.onerror = (error) => {
                    console.warn('[Notifications] WebSocket connection not available (this is normal when running without Daphne/ASGI server)');
                    // Don't log detailed error for 404 - it's expected without ASGI
                    // Close the connection and don't retry aggressively
                    if (this.ws) {
                        this.ws.close();
                    }
                };
            } catch (e) {
                console.warn('[Notifications] Failed to create WebSocket (this is normal if running without Daphne):', e);
                // Fall back to polling or disable notifications
                this.notificationsEnabled = false;
            }
        }

        /**
         * Schedule reconnection attempt
         */
        scheduleReconnect() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('[Notifications] Max reconnection attempts reached');
                return;
            }

            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            console.log(`[Notifications] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, delay);
        }

        /**
         * Handle incoming WebSocket messages
         */
        handleMessage(message) {
            console.log('[Notifications] Received:', message);

            switch (message.type) {
                case 'notification_config':
                    this.handleNotificationConfig(message.data);
                    break;
                case 'flight_notification':
                    this.handleFlightNotification(message);
                    break;
                case 'delay_notification':
                    this.handleDelayNotification(message);
                    break;
                case 'cancellation_notification':
                    this.handleCancellationNotification(message);
                    break;
                case 'gate_change_notification':
                    this.handleGateChangeNotification(message);
                    break;
                case 'notification_permission':
                    console.log('[Notifications] Permission message:', message.message);
                    break;
                default:
                    console.log('[Notifications] Unknown message type:', message.type);
            }
        }

        /**
         * Handle notification config message
         */
        handleNotificationConfig(data) {
            console.log('[Notifications] Config received:', data);
        }

        /**
         * Handle general flight notification
         */
        handleFlightNotification(message) {
            if (!this.notificationPreferences.flight_status) return;
            this.showNotification(message);
        }

        /**
         * Handle flight delay notification
         */
        handleDelayNotification(message) {
            if (!this.notificationPreferences.flight_delay) return;
            this.showNotification(message);
            if (this.notificationPreferences.sound) {
                this.playAlertSound('warning');
            }
        }

        /**
         * Handle flight cancellation notification
         */
        handleCancellationNotification(message) {
            if (!this.notificationPreferences.flight_cancellation) return;
            this.showNotification(message);
            if (this.notificationPreferences.sound) {
                this.playAlertSound('error');
            }
        }

        /**
         * Handle gate change notification
         */
        handleGateChangeNotification(message) {
            if (!this.notificationPreferences.gate_change) return;
            this.showNotification(message);
        }

        /**
         * Show browser notification
         */
        showNotification(message) {
            const { notification, data } = message;

            if (!this.notificationsEnabled || !notification) {
                // Fallback to in-app notification
                this.showInAppNotification(notification || message);
                return;
            }

            const options = {
                body: notification.body || 'Update available',
                icon: notification.icon || '/static/icons/flight.png',
                badge: notification.badge || '/static/icons/badge.png',
                tag: notification.tag || 'default',
                requireInteraction: notification.requireInteraction || false,
                data: data,
                timestamp: message.timestamp
            };

            try {
                const browserNotification = new Notification(notification.title, options);

                browserNotification.onclick = () => {
                    this.handleNotificationClick(data);
                    browserNotification.close();
                };

                browserNotification.onclose = () => {
                    console.log('[Notifications] Notification closed');
                };
            } catch (e) {
                console.error('[Notifications] Failed to show notification:', e);
                this.showInAppNotification(notification || message);
            }
        }

        /**
         * Show in-app notification as fallback
         */
        showInAppNotification(notification) {
            const container = document.getElementById('notification-container');
            if (!container) {
                // Create container if it doesn't exist
                this.createNotificationContainer();
                return this.showInAppNotification(notification);
            }

            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-dismissible fade show';
            alertDiv.setAttribute('role', 'alert');
            alertDiv.setAttribute('aria-live', 'polite');

            // Determine alert type based on notification
            let alertType = 'info';
            let icon = 'info-circle';

            if (notification.type === 'delay_notification' || notification.title?.includes('Delay')) {
                alertType = 'warning';
                icon = 'exclamation-triangle';
            } else if (notification.type === 'cancellation_notification' || notification.title?.includes('Cancel')) {
                alertType = 'danger';
                icon = 'times-circle';
            } else if (notification.type === 'gate_change_notification' || notification.title?.includes('Gate')) {
                alertType = 'info';
                icon = 'door-open';
            }

            alertDiv.classList.add(`alert-${alertType}`);

            const title = notification.title || notification.body || 'Notification';
            const body = notification.body || '';

            alertDiv.innerHTML = `
                <i class="fas fa-${icon} me-2" aria-hidden="true"></i>
                <strong>${this.escapeHtml(title)}</strong>
                ${body ? `<br><small>${this.escapeHtml(body)}</small>` : ''}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;

            // Add to container (newest first)
            container.insertBefore(alertDiv, container.firstChild);

            // Auto-dismiss after 10 seconds (longer for important notifications)
            const dismissDelay = alertType === 'danger' ? 15000 : 10000;
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }, dismissDelay);

            // Announce to screen readers
            if (window.BlueFalcon?.announce) {
                window.BlueFalcon.announce(title);
            }

            // Limit number of visible notifications
            while (container.children.length > 5) {
                container.removeChild(container.lastChild);
            }
        }

        /**
         * Create notification container element
         */
        createNotificationContainer() {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            container.setAttribute('aria-label', 'Notifications');
            document.body.appendChild(container);
        }

        /**
         * Handle notification click
         */
        handleNotificationClick(data) {
            console.log('[Notifications] Notification clicked:', data);

            // Navigate to relevant page based on notification data
            if (data?.flight_id) {
                // Could navigate to flight detail page
                // window.location.href = `/core/flights/${data.flight_id}/`;
            }
        }

        /**
         * Play alert sound
         */
        playAlertSound(type) {
            if (!this.soundEnabled) return;

            try {
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }

                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);

                // Different tones for different alert types
                if (type === 'error') {
                    oscillator.frequency.value = 300;
                    oscillator.type = 'sawtooth';
                    gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
                    oscillator.start(this.audioContext.currentTime);
                    oscillator.stop(this.audioContext.currentTime + 0.5);
                } else {
                    oscillator.frequency.value = 600;
                    oscillator.type = 'sine';
                    gainNode.gain.setValueAtTime(0.2, this.audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
                    oscillator.start(this.audioContext.currentTime);
                    oscillator.stop(this.audioContext.currentTime + 0.3);
                }
            } catch (e) {
                console.error('[Notifications] Failed to play sound:', e);
            }
        }

        /**
         * Initialize event listeners for notification controls
         */
        initEventListeners() {
            // Listen for notification preference changes
            document.addEventListener('notificationPreferencesChanged', (e) => {
                this.notificationPreferences = e.detail;
                this.savePreferences();
            });

            // Listen for theme changes to update notification styling
            document.addEventListener('themeChanged', () => {
                // Update any visible notifications for theme
                const notifications = document.querySelectorAll('#notification-container .alert');
                notifications.forEach(notification => {
                    // Could update styling based on theme
                });
            });
        }

        /**
         * Escape HTML to prevent XSS
         */
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        /**
         * Disconnect from WebSocket
         */
        disconnect() {
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
        }
    }

    // ============================================
    // Notification Preferences Modal
    // ============================================
    class NotificationPreferencesModal {
        constructor(manager) {
            this.manager = manager;
            this.modal = null;
        }

        /**
         * Initialize preferences modal
         */
        init() {
            this.createModal();
            this.loadPreferences();
        }

        /**
         * Create preferences modal HTML
         */
        createModal() {
            const modalHtml = `
                <div class="modal fade" id="notificationPreferencesModal" tabindex="-1" aria-labelledby="notificationPreferencesLabel" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="notificationPreferencesLabel">
                                    <i class="fas fa-bell me-2" aria-hidden="true"></i>Notification Preferences
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="prefDesktop" checked>
                                    <label class="form-check-label" for="prefDesktop">
                                        Desktop Notifications
                                    </label>
                                    <small class="form-text text-muted d-block">Show browser notifications for updates</small>
                                </div>
                                <hr>
                                <h6>Notification Types</h6>
                                <div class="form-check form-switch mb-2">
                                    <input class="form-check-input" type="checkbox" id="prefFlightStatus" checked>
                                    <label class="form-check-label" for="prefFlightStatus">
                                        Flight Status Changes
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-2">
                                    <input class="form-check-input" type="checkbox" id="prefFlightDelay" checked>
                                    <label class="form-check-label" for="prefFlightDelay">
                                        Flight Delays
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-2">
                                    <input class="form-check-input" type="checkbox" id="prefFlightCancellation" checked>
                                    <label class="form-check-label" for="prefFlightCancellation">
                                        Flight Cancellations
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="prefGateChange" checked>
                                    <label class="form-check-label" for="prefGateChange">
                                        Gate Changes
                                    </label>
                                </div>
                                <hr>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="prefSound">
                                    <label class="form-check-label" for="prefSound">
                                        Sound Alerts
                                    </label>
                                    <small class="form-text text-muted d-block">Play sound for important notifications</small>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-primary" id="saveNotificationPrefs">
                                    <i class="fas fa-save me-1" aria-hidden="true"></i>Save Preferences
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Add modal to body
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer.firstElementChild);

            this.modal = document.getElementById('notificationPreferencesModal');

            // Add event listeners
            document.getElementById('saveNotificationPrefs').addEventListener('click', () => this.savePreferences());
        }

        /**
         * Load current preferences into modal
         */
        loadPreferences() {
            const prefs = this.manager.notificationPreferences;
            document.getElementById('prefDesktop').checked = prefs.desktop;
            document.getElementById('prefFlightStatus').checked = prefs.flight_status;
            document.getElementById('prefFlightDelay').checked = prefs.flight_delay;
            document.getElementById('prefFlightCancellation').checked = prefs.flight_cancellation;
            document.getElementById('prefGateChange').checked = prefs.gate_change;
            document.getElementById('prefSound').checked = prefs.sound;
        }

        /**
         * Save preferences from modal
         */
        savePreferences() {
            const prefs = {
                desktop: document.getElementById('prefDesktop').checked,
                flight_status: document.getElementById('prefFlightStatus').checked,
                flight_delay: document.getElementById('prefFlightDelay').checked,
                flight_cancellation: document.getElementById('prefFlightCancellation').checked,
                gate_change: document.getElementById('prefGateChange').checked,
                sound: document.getElementById('prefSound').checked
            };

            this.manager.notificationPreferences = prefs;
            this.manager.savePreferences();

            // Dispatch event
            document.dispatchEvent(new CustomEvent('notificationPreferencesChanged', { detail: prefs }));

            // Show confirmation
            if (window.BlueFalcon?.notify) {
                window.BlueFalcon.notify('Notification preferences saved', 'success');
            }

            // Close modal
            const bsModal = new bootstrap.Modal(this.modal);
            bsModal.hide();
        }

        /**
         * Show preferences modal
         */
        show() {
            this.loadPreferences();
            const bsModal = new bootstrap.Modal(this.modal);
            bsModal.show();
        }
    }

    // ============================================
    // Initialize on DOM Ready
    // ============================================
    const notificationManager = new NotificationManager();
    const preferencesModal = new NotificationPreferencesModal(notificationManager);

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize notification system
        notificationManager.init();
        preferencesModal.init();

        // Add notification bell to navbar if not present
        addNotificationBell();

        // Make notification manager available globally
        window.NotificationManager = notificationManager;
        window.NotificationPreferences = preferencesModal;
    });

    /**
     * Add notification bell icon to navbar
     */
    function addNotificationBell() {
        const navBar = document.querySelector('.navbar-nav');
        if (!navBar) return;

        // Check if bell already exists
        if (document.querySelector('.notification-bell-trigger')) return;

        const bellItem = document.createElement('li');
        bellItem.className = 'nav-item notification-bell-trigger';
        bellItem.innerHTML = `
            <button class="nav-link" type="button" id="notificationBellBtn" aria-label="Notification preferences" title="Notification preferences">
                <i class="fas fa-bell" aria-hidden="true"></i>
            </button>
        `;

        // Insert before theme toggle if exists
        const themeToggle = navBar.querySelector('#themeToggle')?.closest('.nav-item');
        if (themeToggle) {
            navBar.insertBefore(bellItem, themeToggle);
        } else {
            navBar.appendChild(bellItem);
        }

        // Add click handler
        document.getElementById('notificationBellBtn').addEventListener('click', () => {
            preferencesModal.show();
        });
    }

})();
