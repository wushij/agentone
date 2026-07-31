<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  Bell,
  CircleCheckFilled,
  CircleCloseFilled,
  Expand,
  Fold,
  InfoFilled,
  Moon,
  Sunny,
  SwitchButton,
  User,
  WarningFilled
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { confirmAction } from '@/utils/confirm'
import AppThemePicker from '@/components/layout/AppThemePicker.vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useNotifyStore } from '@/stores/notify'
import { useThemeStore } from '@/stores/theme'
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const notifyStore = useNotifyStore()
const themeStore = useThemeStore()

const pageTitle = computed(() => {
  const title = route.meta?.title
  return typeof title === 'string' ? title : 'AgentOne'
})

const avatarLetter = computed(() => {
  const name = userStore.displayName
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    user: '普通用户'
  }
  return map[userStore.role] || userStore.role
})

const showRoleLine = computed(
  () => roleLabel.value && roleLabel.value !== userStore.displayName
)

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    await router.replace('/login')
  } catch {
    /* cancelled */
  }
}

function goProfile() {
  router.push('/profile')
}

async function handleClearNotifications() {
  const ok = await confirmAction({
    title: '清空确认',
    message: '确定要清空通知中心的所有消息通知吗？清空后无法恢复。',
    confirmButtonText: '确定清空',
    type: 'warning'
  })
  if (!ok) return
  notifyStore.clearAll()
}

function formatTime(iso: string): string {
  if (!iso) return ''
  try {
    const date = new Date(iso)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (diff < 60) return '刚刚'
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
    return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  } catch {
    return iso
  }
}

function handleNotificationClick(item: any) {
  notifyStore.markRead(item.id)
  if (item.action?.route) {
    void router.push(item.action.route)
  }
}
</script>

<template>
  <header class="app-header">
    <div class="app-header__left">
      <button type="button" class="app-header__collapse" title="折叠侧边栏" @click="appStore.toggleSidebar()">
        <el-icon :size="18">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="pageTitle !== 'AgentOne'">{{ pageTitle }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="app-header__right">
      <div
        class="ws-status"
        :class="{ 'is-connected': notifyStore.wsConnected, 'is-reconnecting': notifyStore.reconnecting }"
        :title="notifyStore.wsConnected ? '通知服务已连接' : '通知服务未连接'"
      >
        <span class="ws-status__dot" />
        <span class="ws-status__text">{{ notifyStore.wsConnected ? '已连接' : notifyStore.reconnecting ? '重连中' : '未连接' }}</span>
      </div>

      <div v-if="userStore.backendUnavailable" class="app-header__offline">
        <span class="app-header__offline-dot" />
        离线模式
      </div>

      <AppThemePicker
        :current-color="themeStore.themeColor"
        :active-preset-id="themeStore.activePresetId"
        @preset-select="themeStore.setTheme"
        @color-change="themeStore.setCustomColor"
      />

      <button
        type="button"
        class="icon-btn"
        :title="themeStore.isDark ? '切换浅色模式' : '切换深色模式'"
        @click="themeStore.toggleColorMode()"
      >
        <el-icon :size="18">
          <Sunny v-if="themeStore.isDark" />
          <Moon v-else />
        </el-icon>
      </button>
      <!-- 消息通知中心浮窗 -->
      <el-popover
        placement="bottom-end"
        :width="340"
        trigger="click"
        :show-after="0"
        :hide-after="0"
        popper-class="notification-popover-panel"
      >
        <template #reference>
          <button
            type="button"
            class="icon-btn icon-btn--badge"
            :title="notifyStore.unreadCount > 0 ? `${notifyStore.unreadCount} 条未读通知` : '通知中心'"
          >
            <el-icon :size="18"><Bell /></el-icon>
            <span v-if="notifyStore.unreadCount > 0" class="icon-btn__badge">
              {{ notifyStore.unreadCount > 9 ? '9+' : notifyStore.unreadCount }}
            </span>
          </button>
        </template>

        <div class="notif-popover">
          <div class="notif-popover__header">
            <div class="notif-popover__title">
              <span>通知中心</span>
              <el-tag v-if="notifyStore.unreadCount > 0" size="small" type="danger" round>
                {{ notifyStore.unreadCount }} 未读
              </el-tag>
            </div>
            <div class="notif-popover__actions">
              <button
                v-if="notifyStore.unreadCount > 0"
                type="button"
                class="notif-action-btn notif-action-btn--primary"
                @click="notifyStore.markAllRead()"
              >
                全部已读
              </button>
              <button
                v-if="notifyStore.notifications.length > 0"
                type="button"
                class="notif-action-btn notif-action-btn--danger"
                @click="handleClearNotifications"
              >
                清空
              </button>
            </div>
          </div>

          <div class="notif-popover__body">
            <template v-if="notifyStore.notifications.length > 0">
              <div
                v-for="item in notifyStore.notifications"
                :key="item.id"
                class="notif-item"
                :class="{ 'is-unread': !item.read }"
                @click="handleNotificationClick(item)"
              >
                <div class="notif-item__icon" :class="`icon--${item.level}`">
                  <el-icon>
                    <InfoFilled v-if="item.level === 'info'" />
                    <WarningFilled v-if="item.level === 'warning'" />
                    <CircleCloseFilled v-if="item.level === 'error'" />
                    <CircleCheckFilled v-if="item.level === 'success'" />
                  </el-icon>
                </div>
                <div class="notif-item__content">
                  <div class="notif-item__head">
                    <span class="notif-item__title">{{ item.title }}</span>
                    <span class="notif-item__time">{{ formatTime(item.timestamp) }}</span>
                  </div>
                  <div class="notif-item__body">{{ item.body }}</div>
                </div>
                <span v-if="!item.read" class="notif-item__unread-dot" />
              </div>
            </template>
            <div v-else class="notif-popover__empty">
              <el-icon class="empty-icon"><Bell /></el-icon>
              <p>暂无新通知</p>
            </div>
          </div>
        </div>
      </el-popover>

      <el-dropdown trigger="click" @command="(cmd: string) => cmd === 'logout' ? handleLogout() : goProfile()">
        <button type="button" class="user-trigger">
          <div class="user-trigger__avatar">
            <img v-if="userStore.profile?.avatar" :src="userStore.profile.avatar" alt="" />
            <span v-else>{{ avatarLetter }}</span>
          </div>
          <div class="user-trigger__info">
            <span class="user-trigger__name">{{ userStore.displayName }}</span>
            <span v-if="showRoleLine" class="user-trigger__role">{{ roleLabel }}</span>
          </div>
          <el-icon class="user-trigger__arrow"><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--ao-radius-full);
  background: rgba(148, 163, 184, 0.1);
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-muted);
}

.ws-status.is-connected {
  background: var(--ao-success-bg);
  color: var(--ao-success);
}

.ws-status.is-reconnecting {
  background: var(--ao-warning-bg);
  color: var(--ao-warning);
}

.ws-status__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.app-header__offline {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--ao-radius-full);
  background: var(--ao-warning-bg);
  color: var(--ao-warning);
  font-size: 12px;
  font-weight: 600;
}

.app-header__offline-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ao-warning);
}

.icon-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: var(--ao-radius-full);
  border: 1px solid var(--theme-border, var(--ao-border));
  background: transparent;
  color: var(--ao-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 30%, transparent);
  background: var(--theme-primary-muted);
}

.icon-btn__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: var(--ao-radius-full);
  background: var(--ao-danger);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 4px 4px;
  border: 1px solid var(--theme-border, var(--ao-border));
  border-radius: var(--ao-radius-full);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-trigger:hover {
  border-color: color-mix(in srgb, var(--theme-primary) 30%, transparent);
  background: var(--theme-primary-muted);
}

.user-trigger__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--theme-primary-gradient);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  overflow: hidden;
  flex-shrink: 0;
}

.user-trigger__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-trigger__info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}

.user-trigger__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.user-trigger__role {
  font-size: 11px;
  color: var(--ao-text-muted);
  margin-top: 2px;
}

.user-trigger__arrow {
  color: var(--ao-text-muted);
  font-size: 12px;
}

.is-active-theme {
  color: var(--theme-primary) !important;
  font-weight: 700 !important;
}

.notif-popover {
  display: flex;
  flex-direction: column;
}

.notif-popover__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--ao-border, #e2e8f0);
}

.notif-popover__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.notif-popover__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notif-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.notif-action-btn--primary {
  background: rgba(99, 102, 241, 0.08);
  color: var(--theme-primary, #6366f1);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.notif-action-btn--primary:hover {
  background: var(--theme-primary, #6366f1);
  color: #ffffff;
  border-color: var(--theme-primary, #6366f1);
}

.notif-action-btn--danger {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.notif-action-btn--danger:hover {
  background: #ef4444;
  color: #ffffff;
  border-color: #ef4444;
}

.notif-popover__body {
  max-height: 360px;
  overflow-y: auto;
  padding: 6px 0;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s ease;
}

.notif-item:hover {
  background: var(--ao-panel-footer-bg, #f8fafc);
}

.notif-item.is-unread {
  background: rgba(99, 102, 241, 0.04);
}

.notif-item__icon {
  font-size: 18px;
  margin-top: 2px;
}
.notif-item__icon.icon--info {
  color: #3b82f6;
}
.notif-item__icon.icon--warning {
  color: #f59e0b;
}
.notif-item__icon.icon--error {
  color: #ef4444;
}
.notif-item__icon.icon--success {
  color: #10b981;
}

.notif-item__content {
  flex: 1;
  min-width: 0;
}

.notif-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.notif-item__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ao-text-primary);
}

.notif-item__time {
  font-size: 11px;
  color: var(--ao-text-muted, #94a3b8);
}

.notif-item__body {
  font-size: 12px;
  color: var(--ao-text-secondary, #64748b);
  line-height: 1.4;
  word-break: break-all;
}

.notif-item__unread-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
  position: absolute;
  top: 14px;
  right: 12px;
}

.notif-popover__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--ao-text-muted, #94a3b8);
}

.notif-popover__empty .empty-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.notif-popover__empty p {
  font-size: 13px;
  margin: 0;
}
</style>

<style>
.notification-popover-panel {
  border-radius: 16px !important;
  padding: 0 !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
  transition: opacity 0.12s cubic-bezier(0.4, 0, 0.2, 1), transform 0.12s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
</style>
