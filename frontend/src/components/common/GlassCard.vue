<script setup lang="ts">
defineProps<{
  padding?: string
}>()
</script>

<template>
  <section class="glass-card ao-card" :style="{ padding: padding || '24px' }">
    <slot />
  </section>
</template>

<style scoped>
.glass-card {
  /* static card — no hover lift to avoid layout jitter */
}
</style>
