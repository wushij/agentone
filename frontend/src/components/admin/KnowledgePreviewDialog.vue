<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { View } from '@element-plus/icons-vue'
import KnowledgeSegmentCard from '@/components/admin/KnowledgeSegmentCard.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import {
  fetchKnowledgePreview,
  previewKnowledgeDraft,
  type KnowledgeItem,
  type KnowledgePreviewResult
} from '@/api/admin'

const visible = defineModel<boolean>('visible', { default: false })

const props = defineProps<{
  kb?: KnowledgeItem | null
  draft?: Partial<KnowledgeItem> | null
}>()

const loading = ref(false)
const preview = ref<KnowledgePreviewResult | null>(null)
const { page, size, total, resetPage } = usePagination(10)

async function loadPreview() {
  loading.value = true
  preview.value = null
  try {
    const params = { page: page.value, size: size.value }
    if (props.draft) {
      if (!props.draft.fileIds?.length) {
        ElMessage.warning('请先选择关联文件')
        return
      }
      preview.value = await previewKnowledgeDraft(props.draft, params)
    } else if (props.kb?.id) {
      if (!props.kb.fileIds?.length) {
        ElMessage.warning('该知识库暂无关联文件')
        return
      }
      preview.value = await fetchKnowledgePreview(props.kb.id, params)
    }
    if (preview.value) {
      total.value = preview.value.total
    }
  } catch {
    ElMessage.error('分段预览加载失败')
  } finally {
    loading.value = false
  }
}

watch(visible, (open) => {
  if (open) {
    resetPage()
    void loadPreview()
  }
})
</script>

<template>
  <el-dialog
    v-model="visible"
    width="880px"
    class="ao-detail-dialog kb-preview-dialog"
    append-to-body
    destroy-on-close
  >
    <template #header>
      <div class="detail-dialog-header">
        <el-icon class="detail-dialog-header__icon"><View /></el-icon>
        <span class="detail-dialog-header__title">
          分段预览 · {{ preview?.kbName || kb?.name || draft?.name || '' }}
        </span>
      </div>
    </template>

    <div v-loading="loading" class="kb-preview-body">
      <div v-if="preview" class="kb-preview-summary">
        <span>共 {{ preview.total }} 个分段</span>
        <span>分段标识符：{{ preview.segmentDelimiterLabel }}</span>
        <span>最大长度：{{ preview.chunkSize }}</span>
        <span v-if="preview.chunkOverlap">重叠：{{ preview.chunkOverlap }}</span>
      </div>

      <div v-if="preview?.fileErrors?.length" class="kb-preview-errors">
        <p v-for="(err, i) in preview.fileErrors" :key="i">{{ err }}</p>
      </div>

      <div v-if="preview?.segments?.length" class="kb-segment-list">
        <KnowledgeSegmentCard v-for="seg in preview.segments" :key="seg.id" :segment="seg" />
      </div>

      <TablePagination
        v-if="total > 0"
        v-model:page="page"
        v-model:size="size"
        :total="total"
        @change="loadPreview"
      />
    </div>
  </el-dialog>
</template>

<style scoped>
.kb-preview-body {
  min-height: 200px;
}

.kb-preview-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--ao-text-muted);
}

.kb-preview-errors {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  color: var(--el-color-danger);
  font-size: 13px;
}

.kb-segment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 52vh;
  overflow-y: auto;
  margin-bottom: 8px;
}
</style>
