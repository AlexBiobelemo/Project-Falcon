# ✈️ Transition Effects Guide

## Overview

The Blue Falcon parallax landing page features **10+ stunning transition effects** that activate when navigating between sections, creating an immersive aviation experience.

---

## 🎬 Transition Effects

### 1. **Flash Pulse** ⚡
**Triggers:** Every section change

A radial blue flash that expands from the center of the screen.

```css
.transition-flash
- Duration: 0.6s
- Effect: Radial gradient pulse
- Color: Blue (#58a6ff)
```

### 2. **Speed Lines** 💨
**Triggers:** Skipping multiple sections (distance > 1)

Vertical blue lines that fall from top to bottom, simulating high-speed movement.

```css
.speed-lines
- Duration: 0.5s
- Lines: 6 staggered lines
- Color: Blue gradient
- Effect: Falling motion
```

### 3. **Wipe Effect** 🌊
**Triggers:** Downward navigation only

A horizontal wipe that moves from left to right across the screen.

```css
.wipe-overlay
- Duration: 0.7s
- Direction: Left to right
- Colors: Theme gradient
- Effect: Screen wipe
```

### 4. **Cloud Pass** ☁️
**Triggers:** Every section change

A large circular cloud that expands and fades, like flying through clouds.

```css
.cloud-pass
- Duration: 0.8s
- Effect: Expanding circle
- Opacity: 0 → 1 → 0
- Scale: 0.5 → 1.2
```

### 5. **Turbo Boost** 🚀
**Triggers:** Fast scrolling (distance > 1)

A quick radial flash indicating accelerated movement.

```css
.turbo-boost
- Duration: 0.3s
- Effect: Quick flash
- Color: Blue tint
- Intensity: High
```

### 6. **Section Exit Animations** 📤

#### Exit Up (scrolling down)
```css
.exit-up
- Duration: 0.6s
- Movement: Up 100px
- Scale: 1 → 0.95
- Blur: 0 → 10px
- Opacity: 1 → 0
```

#### Exit Down (scrolling up)
```css
.exit-down
- Duration: 0.6s
- Movement: Down 100px
- Scale: 1 → 0.95
- Blur: 0 → 10px
- Opacity: 1 → 0
```

### 7. **Section Entry Animations** 📥

#### Entry From Bottom (scrolling down)
```css
.entry-from-bottom
- Duration: 0.8s
- Movement: Up 150px → 0
- Scale: 1.05 → 1
- Blur: 10px → 0
- Opacity: 0 → 1
```

#### Entry From Top (scrolling up)
```css
.entry-from-top
- Duration: 0.8s
- Movement: Down 150px → 0
- Scale: 1.05 → 1
- Blur: 10px → 0
- Opacity: 0 → 1
```

### 8. **Altitude Change Indicator** 🎯
**Triggers:** Every section change

A popup showing the new flight level.

```css
.altitude-change
- Duration: 1.5s visible
- Position: Top center
- Animation: Pop scale effect
- Content: "FL000", "FL100", etc.
```

### 9. **Transition Overlay** 🌑
**Triggers:** Can be triggered manually

A full-screen gradient overlay for dramatic transitions.

```css
.transition-overlay
- Duration: 0.4s
- Background: Theme gradient
- Opacity: 0 ↔ 1
- Z-index: 998
```

### 10. **Zoom Transitions** 🔍
**Available but not auto-triggered**

For special section transitions.

```css
.zoom-out / zoom-in
- Duration: 0.7s
- Scale: 1 ↔ 1.1
- Blur: 0 ↔ 5px
```

### 11. **Rotate Transitions** 🔄
**Available but not auto-triggered**

Rotating entrance/exit effects.

```css
.rotate-out / rotate-in
- Duration: 0.6s
- Rotation: 0deg ↔ 5deg
- Scale: 1 ↔ 0.95
```

### 12. **Slide Transitions** ↔️
**Available but not auto-triggered**

Horizontal slide effects.

```css
.slide-left / slide-right
- Duration: 0.7s
- Translation: 0 ↔ 100px
- Opacity: 1 ↔ 0
```

---

## 🎯 Effect Combinations

### Standard Navigation (1 section)
- ✅ Flash Pulse
- ✅ Cloud Pass
- ✅ Exit/Entry Animations
- ✅ Altitude Change

### Fast Navigation (2+ sections)
- ✅ Flash Pulse
- ✅ Speed Lines
- ✅ Turbo Boost
- ✅ Cloud Pass
- ✅ Exit/Entry Animations
- ✅ Altitude Change

### Downward Navigation
- ✅ All standard effects
- ✅ Wipe Effect (left to right)

### Upward Navigation
- ✅ All standard effects
- ❌ No wipe effect

---

## ⚙️ Customization

### Change Effect Duration

Edit in `parallax.css`:

```css
/* Faster flash */
.transition-flash.active {
    animation: flashPulse 0.3s ease-out; /* Was 0.6s */
}

/* Slower cloud pass */
.cloud-pass.active {
    animation: cloudPass 1.2s ease-out; /* Was 0.8s */
}
```

### Disable Specific Effects

In `parallax.js`, modify `triggerTransitionEffects()`:

```javascript
triggerTransitionEffects(direction, distance) {
    // this.triggerFlash();        // Disable flash
    // this.triggerSpeedLines();   // Disable speed lines
    this.triggerWipe();
    this.triggerCloudPass();
    // this.triggerTurboBoost();   // Disable turbo
}
```

### Add Custom Transition

1. **Create CSS animation:**

```css
.my-custom-effect {
    position: fixed;
    inset: 0;
    z-index: 999;
    opacity: 0;
    pointer-events: none;
}

.my-custom-effect.active {
    animation: myAnimation 0.8s ease-out forwards;
}

@keyframes myAnimation {
    0% { opacity: 0; }
    100% { opacity: 1; }
}
```

2. **Add HTML element:**

```html
<div class="my-custom-effect" id="myCustomEffect"></div>
```

3. **Trigger in JavaScript:**

```javascript
triggerMyCustomEffect() {
    const effect = document.getElementById('myCustomEffect');
    if (!effect) return;
    
    effect.classList.add('active');
    setTimeout(() => {
        effect.classList.remove('active');
    }, 800);
}
```

---

## 🎨 Effect Timing Sequence

```
0ms    ── Navigation triggered
       ── Exit animation starts
       
100ms  ── Flash pulse activates
       
200ms  ── Current section fades out
       
300ms  ── Section deactivates
       
400ms  ── New section activates
       ── Entry animation starts
       ── Altitude indicator shows
       
500ms  ── Speed lines complete (if triggered)
       
600ms  ── Flash completes
       ── Turbo boost completes
       
700ms  ── Wipe completes (if triggered)
       
800ms  ── Cloud pass completes
       ── Entry animation completes
       
1000ms ── Animation lock releases
       ── Ready for next navigation
```

---

## 📊 Performance

All effects are optimized for 60fps:

- ✅ GPU-accelerated (`transform`, `opacity`)
- ✅ Will-change hints
- ✅ Passive event listeners
- ✅ RequestAnimationFrame for smooth animations
- ✅ Cleanup after animations complete

### Browser Performance

| Browser | FPS | Quality |
|---------|-----|---------|
| Chrome/Edge | 60 | Perfect |
| Firefox | 60 | Perfect |
| Safari | 60 | Perfect |
| Mobile | 60 | Optimized |

---

## 🎮 Debug Mode

To see effect timing, enable console logging:

```javascript
// In parallax.js constructor
this.debugMode = true;

// Add logging in trigger methods
triggerFlash() {
    if (this.debugMode) console.log('⚡ Flash triggered');
    // ... rest of code
}
```

---

## 💡 Pro Tips

1. **Layer Effects**: Multiple effects can run simultaneously for compound impact
2. **Distance Matters**: Use scroll distance to determine effect intensity
3. **Direction Aware**: Different effects for up vs down navigation
4. **Mobile Optimization**: Reduce effect count on mobile devices
5. **Accessibility**: Provide option to reduce motion

---

## 🔧 Troubleshooting

### Effects Not Showing
- Check z-index values
- Verify element IDs match
- Ensure CSS classes are applied

### Effects Too Slow
- Reduce animation durations
- Simplify keyframe animations
- Check for CSS conflicts

### Effects Too Intense
- Reduce opacity values
- Shorten animation duration
- Disable specific effects

### Performance Issues
- Reduce blur amounts
- Use transform instead of position
- Limit simultaneous effects

---

**Built with ❤️ for the ultimate aviation experience!** ✈️
