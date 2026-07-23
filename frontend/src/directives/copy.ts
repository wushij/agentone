/**
 * src/directives/copy.ts — v-copy 快捷复制指令
 */

import type { Directive, DirectiveBinding } from 'vue'
import { ElMessage } from 'element-plus'

export const copyDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    el.style.cursor = 'pointer'
    el.addEventListener('click', () => {
      const text = binding.value || el.innerText
      if (!text) return
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('已复制到剪贴板')
      }).catch(() => {
        ElMessage.error('复制失败')
      })
    })
  },
}
