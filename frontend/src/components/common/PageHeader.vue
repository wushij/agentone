<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps<{
  title: string
  subtitle?: string
  section?: string
}>()

const route = useRoute()
const sectionLabel = computed(() => props.section ?? (route.meta.section as string | undefined))
</script>

<template>
  <div class="page-banner">
    <div class="page-banner__pattern" />
    <div class="page-banner__content">
      <div class="page-banner__line">
        <span v-if="sectionLabel" class="page-banner__section">{{ sectionLabel }}</span>
        <h1 class="page-banner__title">{{ title }}</h1>
        <template v-if="subtitle">
          <span class="page-banner__divider" aria-hidden="true">·</span>
          <p class="page-banner__subtitle">{{ subtitle }}</p>
        </template>
      </div>
      <div v-if="$slots.action || $slots.default" class="page-banner__actions">
        <slot name="action" />
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-banner {
  position: relative;
  margin-bottom: 0;
  padding: 10px 18px;
  border-radius: 10px;
  color: #fff;
  overflow: hidden;
  background: var(
    --theme-primary-gradient,
    linear-gradient(
      135deg,
      var(--theme-primary, #4f46e5) 0%,
      var(--theme-primary-hover, #4338ca) 100%
    )
  );
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: background 0.3s ease, border-color 0.3s ease;
}

.page-banner__pattern {
  position: absolute;
  inset: 0;
  opacity: 0.08;
  background-image: radial-gradient(circle at 20% 50%, #fff 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}

.page-banner__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 32px;
}

.page-banner__line {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.page-banner__section {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.75);
  text-transform: uppercase;
}

.page-banner__title {
  margin: 0;
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1.4;
  font-weight: 700;
  white-space: nowrap;
  color: #ffffff;
}

.page-banner__divider {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.55);
}

.page-banner__subtitle {
  margin: 0;
  min-width: 0;
  font-size: 13px;
  line-height: 1.4;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-banner__actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 10px;
}

.page-banner__actions :deep(.el-button:not(.el-button--primary)) {
  height: 32px !important;
  padding: 0 16px !important;
  border: 1.5px solid rgba(255, 255, 255, 0.75) !important;
  background: transparent !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}

.page-banner__actions :deep(.el-button--primary) {
  background: #fff !important;
  border-color: #fff !important;
  color: var(--theme-primary, #4f46e5) !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.22) !important;
}

.page-banner__actions :deep(.el-button--primary:hover),
.page-banner__actions :deep(.el-button--primary:focus) {
  background: #f1f5f9 !important;
  border-color: #fff !important;
  color: var(--theme-primary, #4f46e5) !important;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.28) !important;
  transform: translateY(-1px);
}

.page-banner__actions :deep(.el-select__wrapper),
.page-banner__actions :deep(.el-select .el-input__wrapper) {
  height: 34px !important;
  min-height: 34px !important;
  background: #ffffff !important;
  border: none !important;
  outline: none !important;
  border-radius: 999px !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12) !important;
  padding: 0 14px !important;
  transform: none !important;
  transition: background-color 0.2s ease, box-shadow 0.2s ease !important;
}

.page-banner__actions :deep(.el-select__wrapper:hover),
.page-banner__actions :deep(.el-select .el-input__wrapper:hover) {
  background: #f8fafc !important;
  border: none !important;
  outline: none !important;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.18) !important;
  transform: none !important;
}

.page-banner__actions :deep(.el-select__wrapper.is-focused),
.page-banner__actions :deep(.el-select__wrapper.is-filterable),
.page-banner__actions :deep(.el-select .el-input__wrapper.is-focus) {
  background: #ffffff !important;
  border: none !important;
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 3px 10px rgba(0, 0, 0, 0.2) !important;
  transform: none !important;
}

.page-banner__actions :deep(.el-select__selected-item),
.page-banner__actions :deep(.el-select__placeholder),
.page-banner__actions :deep(.el-select__placeholder.is-transparent),
.page-banner__actions :deep(.el-select .el-input__inner) {
  color: #0f172a !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  text-shadow: none !important;
}

.page-banner__actions :deep(.el-select .el-input__inner::placeholder) {
  color: #64748b !important;
}

.page-banner__actions :deep(.el-select__caret),
.page-banner__actions :deep(.el-select__icon),
.page-banner__actions :deep(.el-select__prefix),
.page-banner__actions :deep(.el-select__suffix),
.page-banner__actions :deep(.el-select .el-input__suffix-inner),
.page-banner__actions :deep(.el-select .el-input__prefix-inner),
.page-banner__actions :deep(.el-select .el-icon) {
  color: #334155 !important;
  font-size: 14px !important;
  opacity: 1 !important;
}

.page-banner__actions :deep(.el-button .el-icon) {
  color: inherit !important;
}

.page-banner__actions :deep(.btn-icon-plus svg),
.page-banner__actions :deep(.el-icon svg) {
  stroke: currentColor !important;
  stroke-width: 1.4px !important;
  -webkit-text-stroke: 0.8px currentColor !important;
  transform: scale(1.08);
}
</style>
