<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { confirmAction } from '@/utils/confirm'
import { fetchTools, toggleToolStatus } from '@/api/admin'

const tools = ref<Array<{ name: string; description: string; type: string; status: string }>>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    tools.value = await fetchTools()
  } catch (error) {
    ElMessage.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(row: { name: string; status: string }) {
  const enabled = row.status !== 'enabled'
  const action = enabled ? '启用' : '停用'
  const ok = await confirmAction({
    message: `确定要${action}工具「${row.name}」吗？`,
    confirmButtonText: action
  })
  if (!ok) return

  try {
    const res = await toggleToolStatus(row.name, enabled)
    row.status = res.status
    ElMessage.success(`工具已${res.status === 'enabled' ? '开启' : '停用'}`)
  } catch {
    ElMessage.error('切换工具状态失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="view-page">
    <PageHeader title="Tool 管理" subtitle="平台集成工具管理，用于控制 Agent 工作流可调用的工具能力。" />

    <el-card shadow="hover" class="content-card">
      <el-table
        v-loading="loading"
        :data="tools"
        stripe
        border
        highlight-current-row
        header-cell-class-name="table-header-style"
      >
        <el-table-column prop="name" label="工具" min-width="120" align="center">
          <template #default="{ row }">
            <code class="tool-code">{{ row.name }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip align="center" />
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain" round>{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" round>
              {{ row.status === 'enabled' ? '已启用' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button
                size="small"
                :class="['action-btn', row.status === 'enabled' ? 'action-btn--danger' : 'action-btn--success']"
                @click="toggleStatus(row)"
              >
                {{ row.status === 'enabled' ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
