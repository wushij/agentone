<template>
  <div class="base-empty">
    <el-empty :description="description || '暂无数据'" />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  description?: string
}>()
</script>

<style scoped>
.base-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 32px;
}
</style>
