import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { bindAuthRouter } from '@/utils/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true, title: 'AgentOne' },
      children: [
        { path: '', redirect: '/chat' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '首页驾驶舱', permission: 'chat:read' }
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/ChatView.vue'),
          meta: { title: 'AI 对话', permission: 'chat:read', fullBleed: true }
        },
        {
          path: 'chat/:id',
          name: 'chat-detail',
          component: () => import('@/views/ChatView.vue'),
          meta: { title: 'AI 对话', permission: 'chat:read', fullBleed: true }
        },
        {
          path: 'agent',
          name: 'agent',
          component: () => import('@/views/agent/AgentView.vue'),
          meta: { title: 'Agent工作流', permission: 'chat:read' }
        },
        {
          path: 'tools',
          name: 'tools',
          component: () => import('@/views/admin/ToolsView.vue'),
          meta: { title: 'Tool管理', permission: 'tool:manage' }
        },
        {
          path: 'prompts',
          name: 'prompts',
          component: () => import('@/views/admin/PromptsView.vue'),
          meta: { title: 'Prompt管理', permission: 'prompt:manage' }
        },
        {
          path: 'models',
          name: 'models',
          component: () => import('@/views/admin/ModelsView.vue'),
          meta: { title: '模型管理', permission: 'model:manage' }
        },
        {
          path: 'files',
          name: 'files',
          component: () => import('@/views/admin/FilesView.vue'),
          meta: { title: '文件中心', permission: 'config:manage' }
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/views/admin/KnowledgeView.vue'),
          meta: { title: '知识库管理', permission: 'config:manage' }
        },
        {
          path: 'logs',
          name: 'logs',
          component: () => import('@/views/admin/LogsView.vue'),
          meta: { title: '日志中心', permission: 'log:read' }
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/admin/SettingsView.vue'),
          meta: { title: '系统设置', permission: 'config:manage' }
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/admin/UsersView.vue'),
          meta: { title: '用户管理', permission: 'user:manage' }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { title: '个人中心' }
        }
      ]
    }
  ]
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()
  await userStore.hydrate()

  const title = to.meta.title ? `${to.meta.title} - AgentOne` : 'AgentOne'
  document.title = title

  if (to.path === '/login') {
    if (userStore.isAuthenticated) return '/chat'
    return true
  }

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    return `/login?redirect=${encodeURIComponent(to.fullPath)}`
  }

  if (to.meta.permission && !userStore.canAccessPermission(to.meta.permission)) {
    if (!userStore.isAuthenticated) {
      return `/login?redirect=${encodeURIComponent(to.fullPath)}`
    }
    return '/chat'
  }

  return true
})

bindAuthRouter(router)

export default router