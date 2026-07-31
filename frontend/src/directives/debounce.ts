/**
 * src/directives/debounce.ts — v-debounce 点击防抖指令
 */

import type { Directive, DirectiveBinding } from 'vue'

// 修复（§5.4）：在 el 上保存 handler 与 binding 引用，updated 同步最新回调，unmounted 清理监听与定时器，避免陈旧闭包与泄漏。
interface DebounceEl extends HTMLElement {
  _debounceHandler?: (e: Event) => void
  _debounceBinding?: DirectiveBinding
  _debounceTimer?: number | null
}

export const debounceDirective: Directive = {
  mounted(el: DebounceEl, binding: DirectiveBinding) {
    el._debounceBinding = binding
    el._debounceTimer = null
    const delay = Number(binding.arg) || 300
    const handler = (e: Event) => {
      if (el._debounceTimer) clearTimeout(el._debounceTimer)
      el._debounceTimer = window.setTimeout(() => {
        const cb = el._debounceBinding?.value
        if (typeof cb === 'function') cb(e)
      }, delay)
    }
    el._debounceHandler = handler
    el.addEventListener('click', handler)
  },
  updated(el: DebounceEl, binding: DirectiveBinding) {
    // 同步最新 binding，避免回调闭包陈旧
    el._debounceBinding = binding
  },
  unmounted(el: DebounceEl) {
    if (el._debounceTimer) clearTimeout(el._debounceTimer)
    if (el._debounceHandler) el.removeEventListener('click', el._debounceHandler)
    el._debounceHandler = undefined
    el._debounceBinding = undefined
    el._debounceTimer = null
  },
}
