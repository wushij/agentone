<script setup lang="ts">
import LoginBackground from '@/components/auth/LoginBackground.vue'
import LoginBrandPanel from '@/components/auth/LoginBrandPanel.vue'
import LoginFormPanel from '@/components/auth/LoginFormPanel.vue'
</script>

<template>
  <div class="auth-page">
    <LoginBackground />
    <div class="auth-shell">
      <LoginBrandPanel />
      <LoginFormPanel />
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px 24px;
  position: relative;
  overflow: hidden;
  background: radial-gradient(ellipse 120% 100% at 50% 45%, #eef2f8 0%, #dde5f0 40%, #c8d6e8 70%, #b8c9df 100%);
}

.auth-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(340px, 1fr) minmax(400px, 440px);
  width: min(920px, 100%);
  height: 580px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow:
    0 30px 70px rgba(100, 120, 150, 0.15),
    0 10px 30px rgba(100, 120, 150, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

@media (max-width: 840px) {
  .auth-shell {
    grid-template-columns: 1fr;
    max-width: 440px;
    height: auto;
    min-height: 520px;
  }
}
</style>
