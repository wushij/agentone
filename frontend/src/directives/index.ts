/**
 * src/directives/index.ts — 全局自定义指令统一注册插件
 */

import type { App } from 'vue'
import { permissionDirective } from './permission'
import { copyDirective } from './copy'
import { focusDirective } from './focus'
import { debounceDirective } from './debounce'

export function setupDirectives(app: App) {
  app.directive('permission', permissionDirective)
  app.directive('copy', copyDirective)
  app.directive('focus', focusDirective)
  app.directive('debounce', debounceDirective)
}
