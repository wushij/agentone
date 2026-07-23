<template>
  <div class="base-card" :class="{ 'is-hoverable': hoverable }">
    <div v-if="$slots.header || title" class="base-card__header">
      <slot name="header">
        <h3 class="base-card__title">{{ title }}</h3>
      </slot>
    </div>
    <div class="base-card__body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  hoverable?: boolean
}>()
</script>

<style scoped>
.base-card {
  background-color: var(--color-bg-card, #ffffff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.base-card.is-hoverable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--color-primary, #3b82f6);
}

.base-card__title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-main, #111827);
}
</style>
