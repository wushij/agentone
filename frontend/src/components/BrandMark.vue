<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: number
    showText?: boolean
  }>(),
  {
    size: 32,
    showText: false
  }
)
</script>

<template>
  <div class="brand-mark" :class="{ 'brand-mark--with-text': showText }">
    <div class="brand-mark__icon" :style="{ width: `${size}px`, height: `${size}px` }">
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <linearGradient id="brandGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop stop-color="#4f46e5" />
            <stop offset="0.5" stop-color="#3b82f6" />
            <stop offset="1" stop-color="#8b5cf6" />
          </linearGradient>
        </defs>
        <rect width="40" height="40" rx="12" fill="url(#brandGrad)" />
        <path
          d="M12 26V14h4.2l3.8 7.2L23.8 14H28v12h-3.4v-7.4L20.8 26h-2.6l-3.8-7.4V26H12z"
          fill="white"
          fill-opacity="0.95"
        />
        <circle cx="30" cy="12" r="3" fill="white" fill-opacity="0.35" />
      </svg>
    </div>
    <span v-if="showText" class="brand-mark__text">AgentOne</span>
  </div>
</template>

<style scoped>
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.brand-mark__icon {
  flex-shrink: 0;
  border-radius: var(--ao-radius-lg);
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.28);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
}

.brand-mark__icon svg {
  width: 100%;
  height: 100%;
  display: block;
}

.brand-mark--with-text:hover .brand-mark__icon {
  transform: scale(1.04) rotate(-2deg);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.38);
}

.brand-mark__text {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #0f172a 0%, #4f46e5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
