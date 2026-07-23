/**
 * src/directives/permission.ts — v-permission 权限控制指令
 */

import type { Directive, DirectiveBinding } from 'vue'
import { useUserStore } from '@/stores/user'

export const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const userStore = useUserStore()
    if (value && Array.isArray(value) && value.length > 0) {
      const hasPermission = userStore.permissions.some(p => value.includes(p)) || userStore.fullAccess
      if (!hasPermission) {
        el.parentNode?.removeChild(el)
      }
    }
  },
}
