<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Bell, Expand, Fold, Moon, Sunny, SwitchButton, User } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
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

const pageTitle = computed(() => {  const title = route.meta?.title
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

function goNotifications() {
  notifyStore.markAllRead()
  router.push('/dashboard')
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
      <button
        v-if="notifyStore.unreadCount > 0"
        type="button"
        class="icon-btn icon-btn--badge"
        :title="`${notifyStore.unreadCount} 条未读通知`"
        @click="goNotifications"
      >
        <el-icon :size="18"><Bell /></el-icon>
        <span class="icon-btn__badge">{{ notifyStore.unreadCount > 9 ? '9+' : notifyStore.unreadCount }}</span>
      </button>

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
  border-radius: 8px;
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
</style>
