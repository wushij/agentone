/**
 * src/plugins/index.ts — 插件集中注册器
 */

import type { App } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { setupDirectives } from '@/directives'

export function setupPlugins(app: App) {
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)
  setupDirectives(app)
}
