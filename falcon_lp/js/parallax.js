/**
 * Blue Falcon - Parallax Flight Controller
 * Smooth section transitions with aviation-themed effects
 */

class ParallaxFlight {
    constructor() {
        this.sections = [];
        this.currentSection = 0;
        this.isAnimating = false;
        this.scrollDelta = 0;
        this.touchStartY = 0;
        this.wheelTimeout = null;
        this.lastScrollDirection = 0;
        this.scrollVelocity = 0;
        this.transitionType = 'smooth'; // smooth, fade, slide, zoom, rotate
        
        this.init();
    }
    
    init() {
        // Wait for DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        // Get all sections
        this.sections = document.querySelectorAll('.parallax-section');
        this.totalSections = this.sections.length;
        
        // Cache DOM elements
        this.transitionOverlay = document.getElementById('transitionOverlay');
        this.transitionFlash = document.getElementById('transitionFlash');
        this.speedLines = document.getElementById('speedLines');
        this.wipeOverlay = document.getElementById('wipeOverlay');
        this.cloudPass = document.getElementById('cloudPass');
        this.turboBoost = document.getElementById('turboBoost');
        this.altitudeChange = document.getElementById('altitudeChange');
        this.altitudeChangeLevel = document.getElementById('altitudeChangeLevel');
        
        // Create UI elements
        this.createProgressIndicator();
        this.createContrail();
        this.createParticles();
        this.showLoadingScreen();
        
        // Bind events
        this.bindEvents();
        
        // Initialize first section
        this.activateSection(0);
        
        // Hide loading screen
        setTimeout(() => this.hideLoadingScreen(), 2000);
    }
    
    /**
     * Create Flight Progress Indicator
     */
    createProgressIndicator() {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'flight-progress';
        progressContainer.innerHTML = `
            <div class="flight-path">
                <div class="flight-path-fill" id="flightPathFill"></div>
            </div>
        `;
        
        this.sections.forEach((section, index) => {
            const dot = document.createElement('div');
            dot.className = 'progress-dot';
            dot.setAttribute('data-section', section.dataset.name || `Section ${index + 1}`);
            dot.addEventListener('click', () => this.navigateTo(index));
            progressContainer.appendChild(dot);
        });
        
        document.body.appendChild(progressContainer);
        
        // Add airplane indicator
        const airplane = document.createElement('div');
        airplane.className = 'airplane-indicator';
        airplane.innerHTML = '<i class="fas fa-plane"></i>';
        document.body.appendChild(airplane);
        
        // Add altitude display
        const altitude = document.createElement('div');
        altitude.className = 'altitude-display';
        altitude.innerHTML = `
            <div class="altitude-value" id="altitudeValue">FL0</div>
            <div class="altitude-label">Flight Level</div>
        `;
        document.body.appendChild(altitude);
    }
    
    /**
     * Create Contrail Effect
     */
    createContrail() {
        const contrail = document.createElement('div');
        contrail.className = 'contrail';
        document.body.appendChild(contrail);
        this.contrail = contrail;
    }
    
    /**
     * Create Starfield Particles
     */
    createParticles() {
        const particlesContainer = document.querySelector('.particles');
        if (!particlesContainer) return;
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 10}s`;
            particle.style.animationDuration = `${10 + Math.random() * 10}s`;
            particlesContainer.appendChild(particle);
        }
    }
    
    /**
     * Show Loading Screen
     */
    showLoadingScreen() {
        const loading = document.createElement('div');
        loading.className = 'loading-screen';
        loading.id = 'loadingScreen';
        loading.innerHTML = `
            <div class="loading-plane">
                <i class="fas fa-plane"></i>
            </div>
            <div class="loading-text">Preparing for Takeoff</div>
            <div class="loading-bar">
                <div class="loading-progress"></div>
            </div>
        `;
        document.body.appendChild(loading);
    }
    
    /**
     * Hide Loading Screen
     */
    hideLoadingScreen() {
        const loading = document.getElementById('loadingScreen');
        if (loading) {
            loading.classList.add('hidden');
            setTimeout(() => loading.remove(), 500);
        }
        
        // Show scroll hint
        this.showScrollHint();
    }
    
    /**
     * Show Scroll Hint
     */
    showScrollHint() {
        const hint = document.createElement('div');
        hint.className = 'scroll-hint';
        hint.id = 'scrollHint';
        hint.innerHTML = `
            <span>Scroll to explore</span>
            <i class="fas fa-chevron-down"></i>
        `;
        hint.addEventListener('click', () => this.navigateTo(1));
        document.body.appendChild(hint);
        
        // Auto-hide after first scroll
        setTimeout(() => {
            if (hint) hint.remove();
        }, 5000);
    }
    
    /**
     * Bind Event Listeners
     */
    bindEvents() {
        // Wheel event for smooth scrolling
        window.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        
        // Touch events for mobile
        window.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        window.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
        
        // Keyboard navigation
        window.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Resize handler
        window.addEventListener('resize', () => this.handleResize());
        
        // Prevent default scroll behavior
        document.body.addEventListener('wheel', (e) => {
            if (this.isAnimating) e.preventDefault();
        }, { passive: false });
    }
    
    /**
     * Handle Mouse Wheel
     */
    handleWheel(e) {
        e.preventDefault();
        
        if (this.isAnimating) return;
        
        // Accumulate scroll delta
        this.scrollDelta += e.deltaY;
        
        // Threshold for section change
        const threshold = 50;
        
        if (this.scrollDelta > threshold) {
            this.scrollDelta = 0;
            this.navigateNext();
        } else if (this.scrollDelta < -threshold) {
            this.scrollDelta = 0;
            this.navigatePrev();
        }
        
        // Reset delta after delay
        clearTimeout(this.wheelTimeout);
        this.wheelTimeout = setTimeout(() => {
            this.scrollDelta = 0;
        }, 100);
    }
    
    /**
     * Handle Touch Start
     */
    handleTouchStart(e) {
        this.touchStartY = e.touches[0].clientY;
    }
    
    /**
     * Handle Touch End
     */
    handleTouchEnd(e) {
        if (this.isAnimating) return;
        
        const touchEndY = e.changedTouches[0].clientY;
        const diff = this.touchStartY - touchEndY;
        
        if (Math.abs(diff) > 50) {
            if (diff > 0) {
                this.navigateNext();
            } else {
                this.navigatePrev();
            }
        }
    }
    
    /**
     * Handle Keyboard Navigation
     */
    handleKeydown(e) {
        if (this.isAnimating) return;
        
        switch(e.key) {
            case 'ArrowDown':
            case 'PageDown':
            case ' ':
                e.preventDefault();
                this.navigateNext();
                break;
            case 'ArrowUp':
            case 'PageUp':
                e.preventDefault();
                this.navigatePrev();
                break;
            case 'Home':
                e.preventDefault();
                this.navigateTo(0);
                break;
            case 'End':
                e.preventDefault();
                this.navigateTo(this.totalSections - 1);
                break;
        }
    }
    
    /**
     * Handle Resize
     */
    handleResize() {
        // Recalculate if needed
    }
    
    /**
     * Navigate to Next Section
     */
    navigateNext() {
        if (this.currentSection < this.totalSections - 1) {
            this.navigateTo(this.currentSection + 1);
        }
    }
    
    /**
     * Navigate to Previous Section
     */
    navigatePrev() {
        if (this.currentSection > 0) {
            this.navigateTo(this.currentSection - 1);
        }
    }
    
    /**
     * Navigate to Specific Section
     */
    navigateTo(index) {
        if (this.isAnimating || index === this.currentSection) return;
        
        this.isAnimating = true;
        
        // Determine scroll direction
        const direction = index > this.currentSection ? 'down' : 'up';
        const distance = Math.abs(index - this.currentSection);
        
        // Hide scroll hint on first navigation
        const hint = document.getElementById('scrollHint');
        if (hint) hint.remove();
        
        // Calculate scroll velocity for effect intensity
        this.scrollVelocity = distance;
        
        // Trigger transition effects
        this.triggerTransitionEffects(direction, distance);
        
        // Apply exit animation to current section
        this.applyExitAnimation(direction);
        
        // Deactivate current section
        if (this.sections[this.currentSection]) {
            setTimeout(() => {
                this.sections[this.currentSection].classList.remove('active');
                this.sections[this.currentSection].classList.add('previous');
            }, 300);
        }
        
        // Activate new section with entry animation
        setTimeout(() => {
            this.currentSection = index;
            this.activateSection(index);
            this.applyEntryAnimation(direction);
            
            // Update progress indicator
            this.updateProgress();
            
            // Show altitude change indicator
            this.showAltitudeChange(index);
        }, 400);
        
        // Reset animation flag
        setTimeout(() => {
            this.isAnimating = false;
            this.scrollVelocity = 0;
        }, 1000);
    }
    
    /**
     * Trigger Transition Effects
     */
    triggerTransitionEffects(direction, distance) {
        // Flash effect
        this.triggerFlash();
        
        // Speed lines for fast scrolling
        if (distance > 1) {
            this.triggerSpeedLines();
            this.triggerTurboBoost();
        }
        
        // Wipe effect for downward navigation
        if (direction === 'down') {
            this.triggerWipe();
        }
        
        // Cloud pass effect
        this.triggerCloudPass();
    }
    
    /**
     * Trigger Flash Effect
     */
    triggerFlash() {
        if (!this.transitionFlash) return;
        
        this.transitionFlash.classList.add('active');
        setTimeout(() => {
            this.transitionFlash.classList.remove('active');
        }, 600);
    }
    
    /**
     * Trigger Speed Lines
     */
    triggerSpeedLines() {
        if (!this.speedLines) return;
        
        this.speedLines.classList.add('active');
        setTimeout(() => {
            this.speedLines.classList.remove('active');
        }, 500);
    }
    
    /**
     * Trigger Wipe Effect
     */
    triggerWipe() {
        if (!this.wipeOverlay) return;
        
        this.wipeOverlay.classList.add('active');
        setTimeout(() => {
            this.wipeOverlay.classList.remove('active');
        }, 700);
    }
    
    /**
     * Trigger Cloud Pass
     */
    triggerCloudPass() {
        if (!this.cloudPass) return;
        
        this.cloudPass.classList.add('active');
        setTimeout(() => {
            this.cloudPass.classList.remove('active');
        }, 800);
    }
    
    /**
     * Trigger Turbo Boost
     */
    triggerTurboBoost() {
        if (!this.turboBoost) return;
        
        this.turboBoost.classList.add('active');
        setTimeout(() => {
            this.turboBoost.classList.remove('active');
        }, 300);
    }
    
    /**
     * Apply Exit Animation
     */
    applyExitAnimation(direction) {
        const currentSectionEl = this.sections[this.currentSection];
        if (!currentSectionEl) return;
        
        // Remove any existing animation classes
        currentSectionEl.classList.remove('exit-up', 'exit-down', 'zoom-out', 'rotate-out', 'slide-left');
        
        // Force reflow
        void currentSectionEl.offsetWidth;
        
        // Apply appropriate exit animation
        if (direction === 'down') {
            currentSectionEl.classList.add('exit-up');
        } else {
            currentSectionEl.classList.add('exit-down');
        }
        
        // Clean up animation class after completion
        setTimeout(() => {
            currentSectionEl.classList.remove('exit-up', 'exit-down');
        }, 800);
    }
    
    /**
     * Apply Entry Animation
     */
    applyEntryAnimation(direction) {
        const newSectionEl = this.sections[this.currentSection];
        if (!newSectionEl) return;
        
        // Remove any existing animation classes
        newSectionEl.classList.remove('entry-from-bottom', 'entry-from-top', 'zoom-in', 'rotate-in', 'slide-right');
        
        // Force reflow
        void newSectionEl.offsetWidth;
        
        // Apply appropriate entry animation
        if (direction === 'down') {
            newSectionEl.classList.add('entry-from-bottom');
        } else {
            newSectionEl.classList.add('entry-from-top');
        }
        
        // Clean up animation class after completion
        setTimeout(() => {
            newSectionEl.classList.remove('entry-from-bottom', 'entry-from-top');
        }, 800);
    }
    
    /**
     * Show Altitude Change Indicator
     */
    showAltitudeChange(index) {
        if (!this.altitudeChange || !this.altitudeChangeLevel) return;
        
        const flightLevel = (index * 100).toString().padStart(3, '0');
        this.altitudeChangeLevel.textContent = `FL${flightLevel}`;
        
        this.altitudeChange.classList.add('active');
        
        setTimeout(() => {
            this.altitudeChange.classList.remove('active');
        }, 1500);
    }
    
    /**
     * Activate Section
     */
    activateSection(index) {
        const section = this.sections[index];
        if (!section) return;
        
        section.classList.remove('previous');
        section.classList.add('active');
        
        // Show footer on last section
        const footer = document.querySelector('.parallax-footer');
        if (footer) {
            if (index === this.totalSections - 1) {
                footer.classList.add('visible');
            } else {
                footer.classList.remove('visible');
            }
        }
        
        // Trigger counter animation for hero section
        if (index === 0) {
            this.triggerCounterAnimation();
        }
    }
    
    /**
     * Update Progress Indicator
     */
    updateProgress() {
        const dots = document.querySelectorAll('.progress-dot');
        const fill = document.getElementById('flightPathFill');
        const altitude = document.getElementById('altitudeValue');
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === this.currentSection);
        });
        
        // Update flight path fill
        const progress = ((this.currentSection + 1) / this.totalSections) * 100;
        if (fill) {
            fill.style.height = `${progress}%`;
        }
        
        // Update altitude
        if (altitude) {
            altitude.textContent = `FL${(this.currentSection * 100).toString().padStart(3, '0')}`;
        }
    }
    
    /**
     * Animate Contrail
     */
    animateContrail() {
        if (!this.contrail) return;
        
        this.contrail.style.transition = 'left 0.5s ease';
        this.contrail.style.left = '100%';
        
        setTimeout(() => {
            this.contrail.style.transition = 'none';
            this.contrail.style.left = '-100px';
        }, 500);
    }
    
    /**
     * Trigger Counter Animation
     */
    triggerCounterAnimation() {
        const counters = document.querySelectorAll('#hero .stat-number[data-count]');
        if (counters.length === 0) return;
        
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-count'));
            const duration = 2000;
            const step = target / (duration / 16);
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
}

// Initialize parallax flight controller
const flightController = new ParallaxFlight();

// Export for external use
window.ParallaxFlight = ParallaxFlight;
window.flightController = flightController;
