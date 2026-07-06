<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  Connection,
  DataBoard,
  Document,
  Files,
  Folder,
  List,
  Setting,
  Tools,
  User,
  Cpu,
  UserFilled
} from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

interface MenuItem {
  path: string
  label: string
  icon: object
  permission?: string
}

interface MenuGroup {
  label: string
  items: MenuItem[]
}

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const coreGroup: MenuGroup = {
  label: '核心',
  items: [
    { path: '/dashboard', label: '首页驾驶舱', icon: DataBoard, permission: 'chat:read' },
    { path: '/chat', label: 'AI 对话', icon: ChatDotRound, permission: 'chat:read' },
    { path: '/agent', label: 'Agent 工作流', icon: Connection, permission: 'chat:read' }
  ]
}

const adminGroup: MenuGroup = {
  label: '系统管理',
  items: [
    { path: '/tools', label: 'Tool 管理', icon: Tools, permission: 'tool:manage' },
    { path: '/prompts', label: 'Prompt 管理', icon: Document, permission: 'prompt:manage' },
    { path: '/models', label: '模型管理', icon: Cpu, permission: 'model:manage' },
    { path: '/files', label: '文件中心', icon: Files, permission: 'config:manage' },
    { path: '/knowledge', label: '知识库管理', icon: Folder, permission: 'config:manage' },
    { path: '/logs', label: '日志中心', icon: List, permission: 'log:read' },
    { path: '/users', label: '用户管理', icon: UserFilled, permission: 'user:manage' },
    { path: '/profile', label: '个人中心', icon: User },
    { path: '/settings', label: '系统设置', icon: Setting, permission: 'config:manage' }
  ]
}

const visibleCoreItems = computed(() =>
  coreGroup.items.filter((item) => !item.permission || userStore.canAccessPermission(item.permission))
)

const visibleAdminItems = computed(() =>
  adminGroup.items.filter((item) => !item.permission || userStore.canAccessPermission(item.permission))
)

const activeMenu = computed(() => {
  if (route.path.startsWith('/chat')) return '/chat'
  return route.path
})
</script>

<template>
  <aside class="layout-sidebar" :class="{ 'is-collapse': appStore.sidebarCollapsed }">
    <div class="cd-sidebar-logo">
      <BrandMark :size="28" />
      <span v-show="!appStore.sidebarCollapsed" class="cd-logo-text">AgentOne</span>
    </div>

    <div class="menu-wrapper">
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item-group v-if="visibleCoreItems.length" :title="coreGroup.label">
          <el-menu-item v-for="item in visibleCoreItems" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.label }}</template>
          </el-menu-item>
        </el-menu-item-group>

        <el-menu-item-group v-if="visibleAdminItems.length" :title="adminGroup.label">
          <el-menu-item v-for="item in visibleAdminItems" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.label }}</template>
          </el-menu-item>
        </el-menu-item-group>
      </el-menu>
    </div>
  </aside>
</template>
