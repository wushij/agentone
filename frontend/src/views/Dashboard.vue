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
        <div class="header-badge" title="系统实时数据采集已开启">
          <span class="live-dot-wrap">
            <span class="live-dot-pulse"></span>
            <span class="live-dot"></span>
          </span>
          <el-icon :size="14" class="live-icon"><DataAnalysis /></el-icon>
          <span class="live-text">实时数据</span>
        </div>
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
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 14px 5px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.32);
  border-radius: 999px;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: default;
  user-select: none;
}

.header-badge:hover {
  background: rgba(255, 255, 255, 0.24);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
}

.live-dot-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 8px;
  height: 8px;
}

.live-dot {
  width: 6px;
  height: 6px;
  background-color: #34d399;
  border-radius: 50%;
  box-shadow: 0 0 8px #34d399;
}

.live-dot-pulse {
  position: absolute;
  width: 14px;
  height: 14px;
  background-color: rgba(52, 211, 153, 0.6);
  border-radius: 50%;
  animation: live-pulse 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes live-pulse {
  0% {
    transform: scale(0.5);
    opacity: 0.9;
  }
  100% {
    transform: scale(1.8);
    opacity: 0;
  }
}

.live-icon {
  color: #6ee7b7;
}

.live-text {
  letter-spacing: 0.03em;
  font-size: 12px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}
</style>
