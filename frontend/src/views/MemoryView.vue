<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { confirmDelete } from '@/utils/confirm'
import { deleteMemory, fetchMemories, pinMemory, type MemoryItem } from '@/api/memory'

const memories = ref<MemoryItem[]>([])
const loading = ref(false)
const { page, size, total } = usePagination(10)

const kindLabels: Record<string, string> = {
  fact: '事实',
  preference: '偏好',
  episode: '事件',
  skill: '技能'
}

async function loadMemories() {
  loading.value = true
  try {
    const data = await fetchMemories({ page: page.value, size: size.value })
    memories.value = data.records
    total.value = data.total
  } catch {
    memories.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function handleTogglePin(row: MemoryItem) {
  try {
    await pinMemory(row.id, !row.pinned)
    ElMessage.success(row.pinned ? '已取消置顶' : '已置顶')
    await loadMemories()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDelete(row: MemoryItem) {
  const ok = await confirmDelete({
    title: '删除记忆',
    message: '确定删除这条记忆吗？删除后 AI 将不再记得此条内容。'
  })
  if (!ok) return
  try {
    await deleteMemory(row.id)
    ElMessage.success('已删除')
    await loadMemories()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadMemories)
</script>

<template>
  <div class="view-page">
    <PageHeader title="AI 记忆" subtitle="查看、置顶或删除 AI 长期记住的关于你的偏好与事实" />

    <el-card class="ao-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="memories"
        stripe
        border
        empty-text="暂无记忆"
        header-cell-class-name="table-header-style"
        style="width: 100%"
      >
        <el-table-column prop="content" label="记忆内容" min-width="280" show-overflow-tooltip />
        <el-table-column prop="kind" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="light" round>{{ kindLabels[row.kind] || row.kind }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="importance" label="重要度" width="120" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round((row.importance ?? 0) * 100)"
              :stroke-width="8"
              :show-text="false"
            />
          </template>
        </el-table-column>
        <el-table-column prop="accessCount" label="访问次数" width="100" align="center" />
        <el-table-column prop="pinned" label="置顶" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.pinned" color="#f59e0b"><StarFilled /></el-icon>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button
                size="small"
                class="action-btn action-btn--neutral"
                :icon="row.pinned ? StarFilled : Star"
                @click="handleTogglePin(row)"
              >
                {{ row.pinned ? '取消置顶' : '置顶' }}
              </el-button>
              <el-button size="small" class="action-btn action-btn--danger" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="loadMemories" />

      <EmptyState
        v-if="!loading && total === 0"
        title="暂无记忆"
        description="随着对话进行，AI 会自动提取并记住你的偏好与关键事实"
      />
    </el-card>
  </div>
</template>

<style scoped>
.view-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.table-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.muted {
  color: var(--ao-text-secondary, #94a3b8);
}
</style>
