<script setup lang="ts">
import { ChatDotRound, Promotion } from '@element-plus/icons-vue'
import { useDashboard } from '@/composables/useDashboard'

const { recentChats, announcements } = useDashboard()
</script>

<template>
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
</template>

<style scoped>
.content-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  padding: 22px 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.panel-link {
  font-size: 13px;
  color: var(--theme-primary);
  text-decoration: none;
  font-weight: 600;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

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

.activity-item:hover {
  background: rgba(79, 70, 229, 0.05);
}

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

.activity-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.activity-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-desc {
  font-size: 12px;
  color: var(--ao-text-muted);
}

.activity-time {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.announcement-item {
  display: flex;
  gap: 12px;
}

.announcement-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--theme-primary-gradient);
  margin-top: 6px;
  flex-shrink: 0;
}

.announcement-title {
  font-size: 14px;
  font-weight: 700;
}

.announcement-text {
  margin: 4px 0 6px;
  font-size: 13px;
  color: var(--ao-text-secondary);
  line-height: 1.55;
}

.announcement-time {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.empty-panel {
  text-align: center;
  padding: 32px 16px;
  color: var(--ao-text-muted);
}

.empty-panel p {
  margin: 12px 0 16px;
}

@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
