/**
 * src/directives/focus.ts — v-focus 自动聚焦指令
 */

import type { Directive } from 'vue'

export const focusDirective: Directive = {
  mounted(el: HTMLElement) {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.focus()
    } else {
      const input = el.querySelector('input, textarea') as HTMLElement
      input?.focus()
    }
  },
}
