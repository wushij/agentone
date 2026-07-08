<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PromptEditDialog from '@/components/admin/PromptEditDialog.vue'
import PromptCreateDialog from '@/components/admin/PromptCreateDialog.vue'
import PromptPreviewDialog from '@/components/admin/PromptPreviewDialog.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePromptsAdminProvider } from '@/composables/usePromptsAdmin'
import { promptTypeLabel, canDeletePrompt } from '@/utils/promptTypes'

const { prompts, loading, createOpen, openEdit, openPreview, toggleEnabled, remove, page, size, total, load } =
  usePromptsAdminProvider()

function contentSnippet(content: string, max = 72) {
  const text = content.replace(/\s+/g, ' ').trim()
  return text.length > max ? `${text.slice(0, max)}…` : text
}
</script>

<template>
  <div class="view-page">
    <PageHeader title="Prompt 管理" subtitle="系统 Prompt 模板，保存后对话运行时立即加载">
      <template #action>
        <el-button @click="createOpen = true">
          <el-icon class="btn-icon-plus"><Plus /></el-icon>
          新建 Prompt
        </el-button>
      </template>
    </PageHeader>

    <el-card shadow="hover" class="content-card">
      <el-table
        v-loading="loading"
        :data="prompts"
        stripe
        border
        highlight-current-row
        header-cell-class-name="table-header-style"
      >
        <el-table-column prop="name" label="名称" min-width="160" align="center" />
        <el-table-column label="类型" min-width="140" align="center" class-name="prompt-type-col">
          <template #default="{ row }">
            <el-tag effect="plain" size="small" round class="prompt-type-tag">{{ promptTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" round size="small">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容预览" min-width="200" align="center">
          <template #default="{ row }">
            <span class="prompt-snippet">{{ contentSnippet(row.content) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" class="action-btn action-btn--view" @click="openPreview(row)">预览</el-button>
              <el-button size="small" class="action-btn action-btn--edit" @click="openEdit(row)">编辑</el-button>
              <el-button
                size="small"
                :class="['action-btn', row.enabled ? 'action-btn--danger' : 'action-btn--success']"
                @click="toggleEnabled(row)"
              >
                {{ row.enabled ? '停用' : '启用' }}
              </el-button>
              <el-button
                v-if="canDeletePrompt(row)"
                size="small"
                class="action-btn action-btn--danger"
                @click="remove(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="load" />
    </el-card>

    <PromptEditDialog />
    <PromptCreateDialog />
    <PromptPreviewDialog />
  </div>
</template>

<style scoped>
.prompt-snippet {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ao-text-muted);
  font-size: 13px;
}

:deep(.prompt-type-col .cell) {
  overflow: visible;
}

.prompt-type-tag {
  white-space: nowrap;
}
</style>
