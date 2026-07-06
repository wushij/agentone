<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__icon">{{ icon || '✨' }}</div>
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  text-align: center;
  padding: 48px 24px;
}

.empty-state__icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 8px 16px rgba(79, 70, 229, 0.15));
}

.empty-state h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
}

.empty-state p {
  margin: 0 0 20px;
  color: var(--ao-text-muted);
  font-size: 14px;
  line-height: 1.6;
}
</style>
