<script setup lang="ts">

import { computed, onMounted, ref } from 'vue'

import {
  ChatDotRound,
  DataAnalysis,
  Promotion
} from '@element-plus/icons-vue'

import PageHeader from '@/components/common/PageHeader.vue'
import { fetchDashboardStats, type DashboardStats } from '@/api/admin'

import { useChatStore } from '@/stores/chat'

import { useNotifyStore } from '@/stores/notify'

import { useUserStore } from '@/stores/user'



const chatStore = useChatStore()

const notifyStore = useNotifyStore()

const userStore = useUserStore()



const apiStats = ref<DashboardStats>({

  todayConversations: 0,

  totalTokens: 0,

  toolCalls: 0,

  modelStatus: 'online',

  modelName: 'mock-chat',

  recentConversations: []

})



const stats = computed(() => {
  const online = apiStats.value.modelStatus === 'online'
  return [
    {
      title: '今日对话',
      value: apiStats.value.todayConversations || chatStore.conversations.length,
      unit: '条',
      color: '#4f46e5',
      trend: 'flat' as const,
      trendText: '今日会话数'
    },
    {
      title: 'Token 消耗',
      value: apiStats.value.totalTokens || chatStore.totalTokens || 0,
      unit: '',
      color: '#0d9488',
      trend: 'flat' as const,
      trendText: '全平台累计'
    },
    {
      title: 'Tool 调用',
      value: apiStats.value.toolCalls,
      unit: '次',
      color: '#7c3aed',
      trend: 'flat' as const,
      trendText: '历史累计'
    },
    {
      title: '模型状态',
      value: online ? '在线' : '离线',
      unit: '',
      color: online ? '#16a34a' : '#e11d48',
      trend: online ? ('up' as const) : ('down' as const),
      trendText: online ? `当前模型：${apiStats.value.modelName}` : '请检查模型配置'
    }
  ]
})



const weeklyData = computed(() => apiStats.value.weeklyConversations ?? [])



const maxWeekly = computed(() =>

  Math.max(...weeklyData.value.map((d) => d.count), 1)

)



const tokenPercent = computed(() => apiStats.value.tokenUsagePercent ?? 0)



const defaultAnnouncements = [

  {

    id: 'ann_1',

    title: '系统公告',

    body: 'AgentOne V1.0 已上线，欢迎使用企业级 AI 智能体平台。',

    time: '今天'

  }

]



const announcements = computed(() => {

  if (apiStats.value.announcements?.length) {

    return apiStats.value.announcements.map((a) => ({

      id: a.id,

      title: a.title,

      body: a.body,

      time: new Date(a.timestamp).toLocaleDateString('zh-CN')

    }))

  }

  if (notifyStore.announcements.length) {

    return notifyStore.announcements.map((a) => ({

      id: a.id,

      title: a.title,

      body: a.body,

      time: new Date(a.timestamp).toLocaleDateString('zh-CN')

    }))

  }

  return defaultAnnouncements

})



const recentChats = computed(() => {

  if (apiStats.value.recentConversations?.length) {

    return apiStats.value.recentConversations

  }

  return chatStore.conversations.slice(0, 5)

})



const recentActivity = computed(() => notifyStore.recentActivity)



onMounted(async () => {

  void chatStore.fetchConversations()

  try {

    apiStats.value = await fetchDashboardStats()

  } catch {

    /* fallback */

  }

})

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



    <div class="dashboard-metrics-panel">
      <div class="dashboard-metrics">
        <div
          v-for="card in stats"
          :key="card.title"
          class="dashboard-metric"
          :style="{ borderColor: card.color }"
        >
          <div class="dashboard-metric__label">{{ card.title }}</div>
          <div class="dashboard-metric__value-row">
            <span class="dashboard-metric__value" :style="{ color: card.color }">{{ card.value }}</span>
            <span v-if="card.unit" class="dashboard-metric__unit">{{ card.unit }}</span>
          </div>
          <div
            v-if="card.trendText"
            class="dashboard-metric__trend"
            :class="`dashboard-metric__trend--${card.trend}`"
          >
            {{ card.trendText }}
          </div>
        </div>
      </div>
    </div>



    <section class="charts-grid">

      <div class="panel ao-card chart-panel">

        <div class="panel-header">

          <h2>近 7 日对话趋势</h2>

        </div>

        <div v-if="weeklyData.length" class="bar-chart">

          <div v-for="bar in weeklyData" :key="bar.date" class="bar-col">

            <div class="bar-track">

              <div

                class="bar-fill"

                :style="{ height: `${Math.max(8, (bar.count / maxWeekly) * 100)}%` }"

              />

            </div>

            <span class="bar-value">{{ bar.count }}</span>

            <span class="bar-label">{{ bar.date }}</span>

          </div>

        </div>

        <div v-else class="chart-empty">暂无数据</div>

      </div>



      <div class="panel ao-card chart-panel">

        <div class="panel-header">

          <h2>Token 使用占比</h2>

        </div>

        <div class="donut-wrap">

          <svg viewBox="0 0 120 120" class="donut-chart">

            <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(148,163,184,0.15)" stroke-width="14" />

            <circle

              cx="60"

              cy="60"

              r="48"

              fill="none"

              stroke="url(#donut-grad)"

              stroke-width="14"

              stroke-linecap="round"

              :stroke-dasharray="`${tokenPercent * 3.01} 301`"

              transform="rotate(-90 60 60)"

            />

            <defs>

              <linearGradient id="donut-grad" x1="0" y1="0" x2="1" y2="1">

                <stop stop-color="#4f46e5" />

                <stop offset="1" stop-color="#8b5cf6" />

              </linearGradient>

            </defs>

          </svg>

          <div class="donut-center">

            <span class="donut-pct">{{ tokenPercent }}%</span>

            <span class="donut-sub">已使用</span>

          </div>

        </div>

      </div>

    </section>



    <section class="content-grid">

      <div class="panel ao-card">

        <div class="panel-header">

          <h2>最近会话</h2>

          <router-link to="/chat" class="panel-link">查看全部</router-link>

        </div>

        <div v-if="recentChats.length" class="activity-list">

          <router-link

            v-for="chat in recentChats"

            :key="chat.id"

            :to="`/chat/${chat.id}`"

            class="activity-item"

          >

            <div class="activity-icon"><el-icon><ChatDotRound /></el-icon></div>

            <div class="activity-meta">

              <span class="activity-title">{{ chat.title }}</span>

              <span class="activity-desc">{{ chat.messageCount }} 条消息</span>

            </div>

            <span class="activity-time">{{ new Date(chat.updatedAt).toLocaleDateString('zh-CN') }}</span>

          </router-link>

        </div>

        <div v-else class="empty-panel">

          <el-icon :size="40" color="#94a3b8"><ChatDotRound /></el-icon>

          <p>暂无会话记录</p>

          <router-link to="/chat"><el-button type="primary">开始对话</el-button></router-link>

        </div>

      </div>



      <div class="panel ao-card">

        <div class="panel-header">

          <h2>系统公告</h2>

          <el-icon :size="18" color="#f59e0b"><Promotion /></el-icon>

        </div>

        <div class="announcement-list">

          <div v-for="ann in announcements" :key="ann.id" class="announcement-item">

            <div class="announcement-dot" />

            <div class="announcement-body">

              <span class="announcement-title">{{ ann.title }}</span>

              <p class="announcement-text">{{ ann.body }}</p>

              <span class="announcement-time">{{ ann.time }}</span>

            </div>

          </div>

        </div>

      </div>

    </section>



    <section v-if="recentActivity.length" class="panel ao-card activity-panel">

      <div class="panel-header">

        <h2>最近通知</h2>

        <span class="panel-hint">{{ notifyStore.unreadCount }} 条未读</span>

      </div>

      <div class="notify-list">

        <div

          v-for="item in recentActivity"

          :key="item.id"

          class="notify-item"

          :class="{ unread: !item.read }"

          @click="notifyStore.markRead(item.id)"

        >

          <span class="notify-dot" />

          <div class="notify-body">

            <span class="notify-title">{{ item.title }}</span>

            <p class="notify-text">{{ item.body }}</p>

          </div>

          <span class="notify-time">{{ new Date(item.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</span>

        </div>

      </div>

    </section>

  </div>

</template>



<style scoped>

.dashboard { max-width: 1200px; }



.dashboard-header {

  display: flex;

  align-items: flex-start;

  justify-content: space-between;

  margin-bottom: 28px;

  gap: 16px;

}



.dashboard-title { margin: 0 0 6px; font-size: 28px; font-weight: 800; }

.dashboard-subtitle { margin: 0; color: var(--ao-text-secondary); font-size: 14px; }



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

.charts-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  margin-top: 16px;
  margin-bottom: 16px;
}

.chart-panel { padding: 22px 24px; min-height: 220px; }



.bar-chart {

  display: flex;

  align-items: flex-end;

  justify-content: space-between;

  gap: 8px;

  height: 160px;

  padding-top: 8px;

}



.bar-col {

  flex: 1;

  display: flex;

  flex-direction: column;

  align-items: center;

  gap: 6px;

  height: 100%;

}



.bar-track {

  flex: 1;

  width: 100%;

  max-width: 48px;

  display: flex;

  align-items: flex-end;

  background: rgba(79, 70, 229, 0.06);

  border-radius: var(--ao-radius) var(--ao-radius) 0 0;

}



.bar-fill {

  width: 100%;

  border-radius: var(--ao-radius) var(--ao-radius) 0 0;

  background: var(--theme-primary-gradient);

  transition: height 0.6s ease;

  min-height: 8px;

}



.bar-value { font-size: 11px; font-weight: 700; color: var(--theme-primary); }

.bar-label { font-size: 11px; color: var(--ao-text-muted); }



.donut-wrap {

  position: relative;

  display: flex;

  align-items: center;

  justify-content: center;

  height: 160px;

}



.donut-chart { width: 140px; height: 140px; }



.donut-center {

  position: absolute;

  display: flex;

  flex-direction: column;

  align-items: center;

}



.donut-pct { font-size: 26px; font-weight: 800; color: var(--ao-text-primary); }

.donut-sub { font-size: 11px; color: var(--ao-text-muted); }



.chart-empty {

  display: flex;

  align-items: center;

  justify-content: center;

  height: 140px;

  color: var(--ao-text-muted);

  font-size: 13px;

}



.content-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-bottom: 16px; }

.activity-panel { margin-bottom: 24px; }



.panel { padding: 22px 24px; }

.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }

.panel-header h2 { margin: 0; font-size: 16px; font-weight: 700; color: var(--ao-text-primary); }

.panel-link { font-size: 13px; color: var(--theme-primary); text-decoration: none; font-weight: 600; }

.panel-hint { font-size: 12px; color: var(--ao-text-muted); font-weight: 600; }



.activity-list { display: flex; flex-direction: column; gap: 4px; }



.activity-item {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 12px 14px;

  border-radius: var(--ao-radius-lg);

  text-decoration: none;

  color: inherit;

  transition: background 0.2s ease;

}



.activity-item:hover { background: rgba(79, 70, 229, 0.05); }



.activity-icon {

  width: 36px;

  height: 36px;

  border-radius: var(--ao-radius);

  background: var(--theme-primary-muted);

  color: var(--theme-primary);

  display: flex;

  align-items: center;

  justify-content: center;

}



.activity-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }

.activity-title { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.activity-desc { font-size: 12px; color: var(--ao-text-muted); }

.activity-time { font-size: 11px; color: var(--ao-text-muted); }



.announcement-list { display: flex; flex-direction: column; gap: 16px; }

.announcement-item { display: flex; gap: 12px; }

.announcement-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--theme-primary-gradient); margin-top: 6px; flex-shrink: 0; }

.announcement-title { font-size: 14px; font-weight: 700; }

.announcement-text { margin: 4px 0 6px; font-size: 13px; color: var(--ao-text-secondary); line-height: 1.55; }

.announcement-time { font-size: 11px; color: var(--ao-text-muted); }



.notify-list { display: flex; flex-direction: column; gap: 4px; }



.notify-item {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 12px 14px;

  border-radius: var(--ao-radius-lg);

  cursor: pointer;

  transition: background 0.2s ease;

}



.notify-item:hover { background: rgba(79, 70, 229, 0.04); }

.notify-item.unread { background: rgba(79, 70, 229, 0.06); }



.notify-dot {

  width: 8px;

  height: 8px;

  border-radius: 50%;

  background: var(--ao-text-muted);

  flex-shrink: 0;

}



.notify-item.unread .notify-dot { background: var(--theme-primary); }



.notify-body { flex: 1; min-width: 0; }

.notify-title { font-size: 13px; font-weight: 700; }

.notify-text { margin: 2px 0 0; font-size: 12px; color: var(--ao-text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.notify-time { font-size: 11px; color: var(--ao-text-muted); flex-shrink: 0; }



.empty-panel { text-align: center; padding: 32px 16px; color: var(--ao-text-muted); }

.empty-panel p { margin: 12px 0 16px; }



@media (max-width: 1100px) {
  .dashboard-metrics { grid-template-columns: repeat(2, 1fr); }
  .charts-grid, .content-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .dashboard-metrics { grid-template-columns: 1fr; }
}

</style>


