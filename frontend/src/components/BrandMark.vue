<script setup lang="ts">
import { computed } from 'vue'
import { brandIconSrc } from '@/utils/brandIconCache'

const props = withDefaults(
  defineProps<{
    size?: number | string
  }>(),
  { size: 48 }
)

const style = computed(() => {
  const v = props.size
  const px = typeof v === 'number' ? `${v}px` : v
  return { width: px, height: px }
})
</script>

<template>
  <img
    class="brand-mark"
    :src="brandIconSrc"
    alt="AgentOne"
    :style="style"
    draggable="false"
    fetchpriority="high"
    decoding="sync"
  />
</template>

<style scoped>
.brand-mark {
  display: block;
  object-fit: contain;
  flex-shrink: 0;
  user-select: none;
}
</style>
