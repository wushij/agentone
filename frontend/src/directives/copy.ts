/**
 * src/directives/copy.ts — v-copy 快捷复制指令
 */

import type { Directive, DirectiveBinding } from 'vue'
import { ElMessage } from 'element-plus'

// 修复（§5.4）：保存 handler 与最新 binding，updated 同步、unmounted 清理监听，避免陈旧闭包与泄漏。
interface CopyEl extends HTMLElement {
  _copyHandler?: () => void
  _copyBinding?: DirectiveBinding
}

export const copyDirective: Directive = {
  mounted(el: CopyEl, binding: DirectiveBinding) {
    el.style.cursor = 'pointer'
    el._copyBinding = binding
    const handler = () => {
      const text = el._copyBinding?.value || el.innerText
      if (!text) return
      navigator.clipboard
        .writeText(text)
        .then(() => ElMessage.success('已复制到剪贴板'))
        .catch(() => ElMessage.error('复制失败'))
    }
    el._copyHandler = handler
    el.addEventListener('click', handler)
  },
  updated(el: CopyEl, binding: DirectiveBinding) {
    el._copyBinding = binding
  },
  unmounted(el: CopyEl) {
    if (el._copyHandler) el.removeEventListener('click', el._copyHandler)
    el._copyHandler = undefined
    el._copyBinding = undefined
  },
}
