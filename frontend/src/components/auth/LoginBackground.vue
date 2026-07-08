<template>
  <div class="auth-bg">
    <div class="auth-bg-grid" />
    <div class="auth-glow auth-glow-a" />
    <div class="auth-glow auth-glow-b" />
    <div class="auth-glow auth-glow-c" />
  </div>
</template>

<style scoped>
.auth-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(100, 130, 180, 0.09) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100, 130, 180, 0.09) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 90%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 40%, transparent 90%);
}

.auth-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.35;
}

.auth-glow-a {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.3) 0%, transparent 70%);
  top: -150px;
  right: 5%;
  animation: floatGlowA 20s ease-in-out infinite alternate;
}

.auth-glow-b {
  width: 440px;
  height: 440px;
  background: radial-gradient(circle, rgba(196, 181, 253, 0.25) 0%, transparent 70%);
  bottom: -120px;
  left: 2%;
  animation: floatGlowB 18s ease-in-out infinite alternate-reverse;
}

.auth-glow-c {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(244, 143, 177, 0.15) 0%, transparent 70%);
  top: 40%;
  left: 40%;
  transform: translate(-50%, -50%);
  animation: floatGlowC 16s ease-in-out infinite alternate;
}

@keyframes floatGlowA {
  0% { transform: translateY(0) scale(1) rotate(0deg); }
  50% { transform: translateY(40px) scale(1.15) rotate(30deg); }
  100% { transform: translateY(-20px) scale(0.9) rotate(-15deg); }
}

@keyframes floatGlowB {
  0% { transform: translateY(0) scale(1.1) rotate(0deg); }
  50% { transform: translateY(-30px) scale(0.9) rotate(-45deg); }
  100% { transform: translateY(30px) scale(1.05) rotate(15deg); }
}

@keyframes floatGlowC {
  0% { transform: translate(-50%, -50%) scale(0.85) translate(-20px, -20px); }
  50% { transform: translate(-50%, -50%) scale(1.1) translate(35px, 30px); }
  100% { transform: translate(-50%, -50%) scale(0.9) translate(-30px, 15px); }
}
</style>
