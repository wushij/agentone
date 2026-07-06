import { ElMessageBox } from 'element-plus'

export type ConfirmOptions = {
  message: string
  title?: string
  confirmButtonText?: string
  cancelButtonText?: string
  type?: 'warning' | 'info' | 'success' | 'error'
}

/** Returns true when user confirms; false when cancelled or closed. */
export async function confirmAction(options: ConfirmOptions): Promise<boolean> {
  try {
    await ElMessageBox.confirm(options.message, options.title ?? '操作确认', {
      type: options.type ?? 'warning',
      confirmButtonText: options.confirmButtonText ?? '确定',
      cancelButtonText: options.cancelButtonText ?? '取消',
      distinguishCancelAndClose: true
    })
    return true
  } catch {
    return false
  }
}

export async function confirmDelete(messageOrOptions: string | ConfirmOptions): Promise<boolean> {
  const options: ConfirmOptions =
    typeof messageOrOptions === 'string' ? { message: messageOrOptions } : messageOrOptions

  return confirmAction({
    ...options,
    title: options.title ?? '删除确认',
    confirmButtonText: options.confirmButtonText ?? '删除',
    type: 'warning'
  })
}
