<script setup lang="ts">
const page = defineModel<number>('page', { default: 1 })
const size = defineModel<number>('size', { default: 10 })

defineProps<{
  total: number
}>()

const emit = defineEmits<{
  change: []
}>()

function onPageChange() {
  emit('change')
}

function onSizeChange() {
  page.value = 1
  emit('change')
}
</script>

<template>
  <div v-if="total > 0" class="table-pagination">
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="size"
      background
      layout="total, sizes, prev, pager, next"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      @current-change="onPageChange"
      @size-change="onSizeChange"
    />
  </div>
</template>

<style scoped>
.table-pagination {
  display: flex;
  justify-content: flex-start;
  padding: 16px 20px;
  background: transparent;
}

:deep(.el-pagination) {
  --el-pagination-font-size: 13px;
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: var(--theme-primary);
}

/* Pager items */
:deep(.el-pager li) {
  background: var(--ao-surface-muted, #f8fafc) !important;
  color: var(--ao-text-secondary, #64748b) !important;
  border: 1px solid var(--ao-border, rgba(148, 163, 184, 0.15)) !important;
  border-radius: 9999px !important;
  font-weight: 500 !important;
  min-width: 32px !important;
  height: 32px !important;
  line-height: 30px !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  margin: 0 4px !important;
}

:deep(.el-pager li:hover) {
  color: var(--theme-primary, #4f46e5) !important;
  border-color: var(--theme-primary, #4f46e5) !important;
  background: var(--theme-primary-muted, rgba(79, 70, 229, 0.08)) !important;
  transform: translateY(-1px);
}

:deep(.el-pager li.is-active) {
  background: var(--theme-primary-gradient, linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%)) !important;
  color: #ffffff !important;
  border-color: transparent !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.2) !important;
}

/* Prev / Next buttons */
:deep(.btn-prev),
:deep(.btn-next) {
  background: var(--ao-surface-muted, #f8fafc) !important;
  color: var(--ao-text-secondary, #64748b) !important;
  border: 1px solid var(--ao-border, rgba(148, 163, 184, 0.15)) !important;
  border-radius: 9999px !important;
  min-width: 32px !important;
  height: 32px !important;
  padding: 0 !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  margin: 0 4px !important;
}

:deep(.btn-prev:hover),
:deep(.btn-next:hover) {
  color: var(--theme-primary, #4f46e5) !important;
  border-color: var(--theme-primary, #4f46e5) !important;
  background: var(--theme-primary-muted, rgba(79, 70, 229, 0.08)) !important;
  transform: translateY(-1px);
}

:deep(.btn-prev:disabled),
:deep(.btn-next:disabled) {
  background: var(--ao-surface-muted, #f8fafc) !important;
  color: var(--ao-text-muted, #94a3b8) !important;
  border-color: var(--ao-border, rgba(148, 163, 184, 0.1)) !important;
  opacity: 0.6 !important;
  transform: none !important;
  cursor: not-allowed !important;
}

/* Total count */
:deep(.el-pagination__total) {
  color: var(--ao-text-secondary, #64748b) !important;
  font-weight: 500 !important;
  margin-right: 16px !important;
}

/* Sizes dropdown */
:deep(.el-select) {
  width: 110px !important;
}

:deep(.el-select__wrapper) {
  border-radius: 9999px !important;
  border: 1px solid var(--ao-border, rgba(148, 163, 184, 0.15)) !important;
  background: var(--ao-surface-muted, #f8fafc) !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
  color: var(--ao-text-secondary, #64748b) !important;
  padding: 0 12px !important;
}

:deep(.el-select__wrapper:hover) {
  border-color: var(--theme-primary, #4f46e5) !important;
}
</style>
