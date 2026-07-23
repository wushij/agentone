<script setup lang="ts">
import { DataAnalysis } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardMetricsPanel from '@/components/dashboard/DashboardMetricsPanel.vue'
import DashboardChartsGrid from '@/components/dashboard/DashboardChartsGrid.vue'
import DashboardContentGrid from '@/components/dashboard/DashboardContentGrid.vue'
import DashboardNotifyPanel from '@/components/dashboard/DashboardNotifyPanel.vue'
import { useDashboardProvider } from '@/composables/useDashboard'

const { userStore } = useDashboardProvider()
</script>

<template>
  <div class="dashboard view-page">
    <PageHeader :title="`欢迎回来，${userStore.displayName}`" subtitle="这是您的 AgentOne 工作台概览">
      <template #action>
        <span class="header-badge">
          <el-icon :size="18"><DataAnalysis /></el-icon>
          <span>实时数据</span>
        </span>
      </template>
    </PageHeader>

    <DashboardMetricsPanel />
    <DashboardChartsGrid />
    <DashboardContentGrid />
    <DashboardNotifyPanel />
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.header-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: var(--ao-radius-full);
}
</style>
