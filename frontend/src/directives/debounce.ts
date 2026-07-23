/**
 * src/directives/debounce.ts — v-debounce 点击防抖指令
 */

import type { Directive, DirectiveBinding } from 'vue'

export const debounceDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    let timer: number | null = null
    const delay = Number(binding.arg) || 300
    el.addEventListener('click', (e) => {
      if (timer) clearTimeout(timer)
      timer = window.setTimeout(() => {
        if (typeof binding.value === 'function') {
          binding.value(e)
        }
      }, delay)
    })
  },
}
