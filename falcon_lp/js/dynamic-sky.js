/**
 * Blue Falcon - Dynamic Sky Animation System
 * Live aircraft, moving clouds, stars, and atmospheric effects
 */

class DynamicSky {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.aircraft = [];
        this.clouds = [];
        this.stars = [];
        this.trails = [];
        this.particles = [];
        this.animationId = null;
        this.lastTime = 0;
        this.mouseX = 0;
        this.mouseY = 0;
        
        // Wait for DOM then initialize
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        console.log('🦅 Dynamic Sky Initializing...');
        this.createCanvas();
        this.createAircraft();
        this.createClouds();
        this.createStars();
        this.bindEvents();
        this.animate();
        console.log('✓ Dynamic Sky Ready - Aircraft:', this.aircraft.length, 'Clouds:', this.clouds.length, 'Stars:', this.stars.length);
    }
    
    createCanvas() {
        this.canvas = document.getElementById('dynamicSkyCanvas');
        if (!this.canvas) {
            console.error('Canvas not found!');
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        console.log('✓ Canvas created:', this.canvas.width, 'x', this.canvas.height);
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    bindEvents() {
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });
    }
    
    createAircraft() {
        // Create multiple aircraft with different flight paths
        const aircraftCount = 5;
        
        for (let i = 0; i < aircraftCount; i++) {
            this.aircraft.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height * 0.6,
                speed: 0.5 + Math.random() * 0.5,
                size: 2 + Math.random() * 2,
                angle: Math.random() * Math.PI * 2,
                trailTimer: 0,
                wingAngle: 0,
                type: Math.floor(Math.random() * 3), // 0: jet, 1: propeller, 2: glider
                color: `hsl(${200 + Math.random() * 40}, 70%, 60%)`,
                blinkTimer: Math.random() * 100
            });
        }
    }
    
    createClouds() {
        const cloudCount = 30;
        
        for (let i = 0; i < cloudCount; i++) {
            this.clouds.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                speedX: 0.1 + Math.random() * 0.2,
                speedY: 0.05 + Math.random() * 0.1,
                size: 30 + Math.random() * 70,
                opacity: 0.1 + Math.random() * 0.2,
                puffs: []
            });
            
            // Create cloud puffs
            const puffCount = 5 + Math.floor(Math.random() * 5);
            for (let j = 0; j < puffCount; j++) {
                this.clouds[i].puffs.push({
                    offsetX: (Math.random() - 0.5) * 100,
                    offsetY: (Math.random() - 0.5) * 30,
                    size: 20 + Math.random() * 40
                });
            }
        }
    }
    
    createStars() {
        const starCount = 200;
        
        for (let i = 0; i < starCount; i++) {
            this.stars.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 2,
                brightness: Math.random(),
                twinkleSpeed: 0.02 + Math.random() * 0.03,
                twinkleDir: Math.random() > 0.5 ? 1 : -1
            });
        }
    }
    
    createTrail(x, y, angle, color) {
        this.trails.push({
            x: x,
            y: y,
            angle: angle,
            age: 0,
            maxAge: 100 + Math.random() * 50,
            width: 3 + Math.random() * 2,
            color: color,
            opacity: 0.6
        });
    }
    
    createParticle(x, y, type = 'spark') {
        const particle = {
            x: x,
            y: y,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            age: 0,
            maxAge: 50 + Math.random() * 50,
            size: 1 + Math.random() * 2,
            type: type,
            color: type === 'spark' ? '#58a6ff' : '#ffffff',
            gravity: type === 'spark' ? 0.02 : 0
        };
        
        this.particles.push(particle);
    }
    
    drawAircraft(aircraft) {
        const ctx = this.ctx;
        const { x, y, size, angle, type, color, wingAngle } = aircraft;
        
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        
        // Draw contrail
        if (type === 0) { // Jet
            ctx.beginPath();
            ctx.moveTo(-size * 3, 0);
            ctx.lineTo(-size * 8, 0);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = size * 0.3;
            ctx.stroke();
        }
        
        // Draw aircraft body
        ctx.fillStyle = color;
        
        if (type === 0) { // Jet
            // Fuselage
            ctx.beginPath();
            ctx.ellipse(0, 0, size * 3, size * 0.5, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Wings
            ctx.beginPath();
            ctx.moveTo(-size, 0);
            ctx.lineTo(-size * 2, -size * 2.5);
            ctx.lineTo(size, 0);
            ctx.lineTo(-size * 2, size * 2.5);
            ctx.closePath();
            ctx.fill();
            
            // Tail
            ctx.beginPath();
            ctx.moveTo(-size * 2.5, 0);
            ctx.lineTo(-size * 3.5, -size);
            ctx.lineTo(-size * 2, 0);
            ctx.lineTo(-size * 3.5, size);
            ctx.closePath();
            ctx.fill();
            
            // Cockpit
            ctx.fillStyle = '#87ceeb';
            ctx.beginPath();
            ctx.ellipse(size * 2, 0, size * 0.8, size * 0.3, 0, 0, Math.PI * 2);
            ctx.fill();
            
        } else if (type === 1) { // Propeller
            // Fuselage
            ctx.beginPath();
            ctx.ellipse(0, 0, size * 2.5, size * 0.4, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Wings
            ctx.fillRect(-size, -size * 2, size * 2, size * 4);
            
            // Propeller
            ctx.strokeStyle = '#silver';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(size * 2.5, -size * 1.5 * Math.sin(wingAngle));
            ctx.lineTo(size * 2.5, size * 1.5 * Math.sin(wingAngle));
            ctx.stroke();
            
        } else { // Glider
            // Long wings
            ctx.beginPath();
            ctx.moveTo(-size * 2, 0);
            ctx.lineTo(size * 4, -size * 0.5);
            ctx.lineTo(size * 4, size * 0.5);
            ctx.closePath();
            ctx.fill();
            
            // Tail
            ctx.beginPath();
            ctx.moveTo(-size * 2, 0);
            ctx.lineTo(-size * 3, -size);
            ctx.lineTo(-size * 1.5, 0);
            ctx.lineTo(-size * 3, size);
            ctx.closePath();
            ctx.fill();
        }
        
        // Navigation lights (blinking)
        aircraft.blinkTimer++;
        const blink = Math.sin(aircraft.blinkTimer * 0.1) > 0;
        
        // Left wing - red
        ctx.fillStyle = blink ? '#ff0000' : '#550000';
        ctx.beginPath();
        ctx.arc(-size, -size * 2, size * 0.3, 0, Math.PI * 2);
        ctx.fill();
        
        // Right wing - green
        ctx.fillStyle = blink ? '#00ff00' : '#005500';
        ctx.beginPath();
        ctx.arc(-size, size * 2, size * 0.3, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    drawCloud(cloud) {
        const ctx = this.ctx;
        const { x, y, puffs, opacity } = cloud;
        
        ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
        
        puffs.forEach(puff => {
            ctx.beginPath();
            ctx.arc(x + puff.offsetX, y + puff.offsetY, puff.size, 0, Math.PI * 2);
            ctx.fill();
        });
    }
    
    drawStar(star) {
        const ctx = this.ctx;
        const { x, y, size, brightness } = star;
        
        ctx.fillStyle = `rgba(255, 255, 255, ${brightness})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
    }
    
    drawTrail(trail) {
        const ctx = this.ctx;
        const { x, y, angle, width, color, opacity, age, maxAge } = trail;
        
        const trailLength = 50 * (1 - age / maxAge);
        
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        
        const gradient = ctx.createLinearGradient(0, 0, -trailLength, 0);
        gradient.addColorStop(0, color.replace(')', `, ${opacity})`));
        gradient.addColorStop(1, color.replace(')', ', 0)'));
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = width;
        ctx.lineCap = 'round';
        
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-trailLength, 0);
        ctx.stroke();
        
        ctx.restore();
    }
    
    drawParticle(particle) {
        const ctx = this.ctx;
        const { x, y, size, color, type } = particle;
        
        ctx.fillStyle = color;
        ctx.beginPath();
        
        if (type === 'spark') {
            // Diamond shape for sparks
            ctx.moveTo(x, y - size);
            ctx.lineTo(x + size, y);
            ctx.lineTo(x, y + size);
            ctx.lineTo(x - size, y);
        } else {
            // Circle for normal particles
            ctx.arc(x, y, size, 0, Math.PI * 2);
        }
        
        ctx.closePath();
        ctx.fill();
    }
    
    updateAircraft(deltaTime) {
        this.aircraft.forEach((aircraft, index) => {
            // Move aircraft
            aircraft.x += Math.cos(aircraft.angle) * aircraft.speed;
            aircraft.y += Math.sin(aircraft.angle) * aircraft.speed;
            
            // Create trail
            aircraft.trailTimer++;
            if (aircraft.trailTimer > 10) {
                this.createTrail(
                    aircraft.x - Math.cos(aircraft.angle) * aircraft.size * 2,
                    aircraft.y - Math.sin(aircraft.angle) * aircraft.size * 2,
                    aircraft.angle,
                    'rgba(135, 206, 235, 0.6)'
                );
                aircraft.trailTimer = 0;
            }
            
            // Update wing angle
            aircraft.wingAngle += 0.3;
            
            // Wrap around screen
            if (aircraft.x < -100) aircraft.x = this.canvas.width + 100;
            if (aircraft.x > this.canvas.width + 100) aircraft.x = -100;
            if (aircraft.y < -100) aircraft.y = this.canvas.height + 100;
            if (aircraft.y > this.canvas.height + 100) aircraft.y = -100;
            
            // Occasionally change direction
            if (Math.random() < 0.001) {
                aircraft.angle += (Math.random() - 0.5) * 0.5;
            }
            
            // Create particles occasionally
            if (Math.random() < 0.05) {
                this.createParticle(
                    aircraft.x + Math.cos(aircraft.angle) * aircraft.size * 3,
                    aircraft.y + Math.sin(aircraft.angle) * aircraft.size * 3,
                    'spark'
                );
            }
        });
    }
    
    updateClouds(deltaTime) {
        this.clouds.forEach(cloud => {
            cloud.x += cloud.speedX;
            cloud.y += cloud.speedY;
            
            // Wrap around
            if (cloud.x > this.canvas.width + 200) {
                cloud.x = -200;
            }
            if (cloud.x < -200) {
                cloud.x = this.canvas.width + 200;
            }
            if (cloud.y > this.canvas.height + 100) {
                cloud.y = -100;
            }
            if (cloud.y < -100) {
                cloud.y = this.canvas.height + 100;
            }
        });
    }
    
    updateStars(deltaTime) {
        this.stars.forEach(star => {
            // Twinkle effect
            star.brightness += star.twinkleSpeed * star.twinkleDir;
            
            if (star.brightness > 1) {
                star.brightness = 1;
                star.twinkleDir = -1;
            } else if (star.brightness < 0.3) {
                star.brightness = 0.3;
                star.twinkleDir = 1;
            }
        });
    }
    
    updateTrails(deltaTime) {
        for (let i = this.trails.length - 1; i >= 0; i--) {
            const trail = this.trails[i];
            trail.age++;
            
            if (trail.age > trail.maxAge) {
                this.trails.splice(i, 1);
            }
        }
    }
    
    updateParticles(deltaTime) {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += particle.gravity;
            particle.age++;
            
            if (particle.age > particle.maxAge) {
                this.particles.splice(i, 1);
            }
        }
    }
    
    draw() {
        const ctx = this.ctx;
        
        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw stars (background layer)
        this.stars.forEach(star => this.drawStar(star));
        
        // Draw trails
        this.trails.forEach(trail => this.drawTrail(trail));
        
        // Draw clouds (mid layer)
        this.clouds.forEach(cloud => this.drawCloud(cloud));
        
        // Draw aircraft
        this.aircraft.forEach(aircraft => this.drawAircraft(aircraft));
        
        // Draw particles (foreground layer)
        this.particles.forEach(particle => this.drawParticle(particle));
    }
    
    animate(currentTime = 0) {
        const deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;
        
        // Update all elements
        this.updateAircraft(deltaTime);
        this.updateClouds(deltaTime);
        this.updateStars(deltaTime);
        this.updateTrails(deltaTime);
        this.updateParticles(deltaTime);
        
        // Draw everything
        this.draw();
        
        // Continue animation
        this.animationId = requestAnimationFrame((time) => this.animate(time));
    }
    
    addAircraft(x, y, angle) {
        this.aircraft.push({
            x: x,
            y: y,
            speed: 2 + Math.random(),
            size: 3 + Math.random() * 2,
            angle: angle || Math.random() * Math.PI * 2,
            trailTimer: 0,
            wingAngle: 0,
            type: Math.floor(Math.random() * 3),
            color: `hsl(${200 + Math.random() * 60}, 80%, 65%)`,
            blinkTimer: 0
        });
    }
    
    createExplosion(x, y, count = 20) {
        for (let i = 0; i < count; i++) {
            this.createParticle(x, y, 'spark');
        }
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas) {
            this.canvas.remove();
        }
    }
}

// Initialize when DOM is ready
let dynamicSky;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        dynamicSky = new DynamicSky();
        window.dynamicSky = dynamicSky;
    });
} else {
    dynamicSky = new DynamicSky();
    window.dynamicSky = dynamicSky;
}

// Export for external use
window.DynamicSky = DynamicSky;
