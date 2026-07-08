<script setup lang="ts">
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'
import { usePromptsAdmin } from '@/composables/usePromptsAdmin'
import { renderMarkdown } from '@/utils/markdown'
import { promptTypeLabel } from '@/utils/promptTypes'

const { previewVisible, previewing } = usePromptsAdmin()

const previewHtml = computed(() =>
  previewing.value?.content ? renderMarkdown(previewing.value.content) : ''
)
</script>

<template>
  <el-dialog
    v-model="previewVisible"
    width="760px"
    class="ao-detail-dialog prompt-preview-dialog"
    append-to-body
    destroy-on-close
  >
    <template #header>
      <div class="detail-dialog-header">
        <el-icon class="detail-dialog-header__icon"><View /></el-icon>
        <span class="detail-dialog-header__title">
          Prompt 预览{{ previewing ? ` · ${previewing.name}` : '' }}
        </span>
      </div>
    </template>

    <template v-if="previewing">
      <div class="prompt-preview-meta">
        <div class="prompt-preview-meta__item">
          <span class="prompt-preview-meta__label">名称</span>
          <span class="prompt-preview-meta__val code-highlight">{{ previewing.name }}</span>
        </div>
        <div class="prompt-preview-meta__item">
          <span class="prompt-preview-meta__label">类型</span>
          <span class="prompt-preview-meta__val">{{ promptTypeLabel(previewing.type) }}</span>
        </div>
        <div class="prompt-preview-meta__item">
          <span class="prompt-preview-meta__label">版本</span>
          <span class="prompt-preview-meta__val">v{{ previewing.version }}</span>
        </div>
        <div class="prompt-preview-meta__item">
          <span class="prompt-preview-meta__label">状态</span>
          <el-tag :type="previewing.enabled ? 'success' : 'info'" round size="small">
            {{ previewing.enabled ? '启用' : '停用' }}
          </el-tag>
        </div>
      </div>

      <div class="detail-content-block">
        <div class="detail-content-block__label">内容预览</div>
        <div
          v-if="previewHtml"
          class="chat-markdown prompt-preview-markdown"
          v-html="previewHtml"
        />
        <div v-else class="prompt-preview-empty">（无内容）</div>
      </div>
    </template>

    <template #footer>
      <div class="detail-dialog-footer">
        <el-button class="detail-dialog-footer__cancel" @click="previewVisible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.prompt-preview-meta {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  margin-bottom: 16px;
  border: 1px solid var(--ao-surface-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--ao-surface-border);
}

.prompt-preview-meta__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 72px;
  padding: 12px 10px;
  background: var(--ao-surface-muted);
  text-align: center;
}

.prompt-preview-meta__label {
  font-size: 12px;
  color: var(--ao-text-muted);
  font-weight: 500;
}

.prompt-preview-meta__val {
  font-size: 14px;
  font-weight: 600;
  color: var(--ao-text-primary);
  word-break: break-all;
}

.prompt-preview-meta__val.code-highlight {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  color: var(--theme-primary);
}

.prompt-preview-markdown {
  max-height: 52vh;
  overflow: auto;
  padding: 16px 18px;
  background: var(--ao-surface-muted);
  text-align: left;
}

.prompt-preview-empty {
  padding: 24px;
  text-align: center;
  color: var(--ao-text-muted);
  font-size: 13px;
}

@media (max-width: 640px) {
  .prompt-preview-meta {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
