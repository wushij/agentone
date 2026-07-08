import { inject, onMounted, provide, ref, type InjectionKey, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import { usePagination } from '@/composables/usePagination'
import {
  createPrompt,
  deletePrompt,
  fetchPrompts,
  setPromptEnabled,
  updatePrompt,
  fetchPromptHistory,
  rollbackPrompt,
  type PromptItem,
  type PromptHistoryItem
} from '@/api/admin'

export interface PromptsAdminContext {
  prompts: Ref<PromptItem[]>
  editVisible: Ref<boolean>
  createOpen: Ref<boolean>
  editing: Ref<{ name: string; content: string } | null>
  newPrompt: Ref<{ name: string; content: string; type: string }>
  previewVisible: Ref<boolean>
  previewing: Ref<PromptItem | null>
  loading: Ref<boolean>
  page: Ref<number>
  size: Ref<number>
  total: Ref<number>
  historyList: Ref<PromptHistoryItem[]>
  loadingHistory: Ref<boolean>
  historyPage: Ref<number>
  historySize: Ref<number>
  historyTotal: Ref<number>
  load: () => Promise<void>
  loadHistory: () => Promise<void>
  openEdit: (row: PromptItem) => Promise<void>
  openPreview: (row: PromptItem) => void
  handleRollback: (ver: number) => Promise<void>
  save: () => Promise<void>
  create: () => Promise<void>
  toggleEnabled: (row: PromptItem) => Promise<void>
  remove: (row: PromptItem) => Promise<void>
}

export const PROMPTS_ADMIN_KEY: InjectionKey<PromptsAdminContext> = Symbol('promptsAdmin')

export function usePromptsAdminProvider(): PromptsAdminContext {
  const prompts = ref<PromptItem[]>([])
  const editVisible = ref(false)
  const previewVisible = ref(false)
  const previewing = ref<PromptItem | null>(null)
  const createOpen = ref(false)
  const editing = ref<{ name: string; content: string } | null>(null)
  const newPrompt = ref({ name: '', content: '', type: 'custom' })
  const loading = ref(false)
  const historyList = ref<PromptHistoryItem[]>([])
  const loadingHistory = ref(false)
  const { page, size, total } = usePagination(10)
  const {
    page: historyPage,
    size: historySize,
    total: historyTotal,
    resetPage: resetHistoryPage
  } = usePagination(10)

  async function load() {
    loading.value = true
    try {
      const data = await fetchPrompts({ page: page.value, size: size.value })
      prompts.value = data.records
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function loadHistory() {
    if (!editing.value) return
    loadingHistory.value = true
    try {
      const data = await fetchPromptHistory(editing.value.name, {
        page: historyPage.value,
        size: historySize.value
      })
      historyList.value = data.records
      historyTotal.value = data.total
    } catch {
      historyList.value = []
      historyTotal.value = 0
    } finally {
      loadingHistory.value = false
    }
  }

  function openPreview(row: PromptItem) {
    previewing.value = row
    previewVisible.value = true
  }

  async function openEdit(row: PromptItem) {
    editing.value = { name: row.name, content: row.content }
    editVisible.value = true
    historyList.value = []
    resetHistoryPage()
    await loadHistory()
  }

  async function handleRollback(ver: number) {
    if (!editing.value) return
    try {
      await ElMessageBox.confirm(`确定要将 "${editing.value.name}" 回滚至版本 v${ver} 吗？`, '版本回滚确认', {
        confirmButtonText: '确定回滚',
        cancelButtonText: '取消',
        type: 'warning'
      })
      const updated = await rollbackPrompt(editing.value.name, ver)
      editing.value.content = updated.content
      ElMessage.success('已回滚至选定版本')
      await loadHistory()
      await load()
    } catch {
      /* cancelled */
    }
  }

  async function save() {
    if (!editing.value) return
    const ok = await confirmAction({
      message: `确定要保存 Prompt「${editing.value.name}」吗？保存后运行时立即生效。`,
      confirmButtonText: '保存'
    })
    if (!ok) return

    await updatePrompt(editing.value.name, editing.value.content)
    ElMessage.success('已保存，运行时立即生效')
    editVisible.value = false
    await load()
  }

  async function create() {
    if (!newPrompt.value.name || !newPrompt.value.content) {
      ElMessage.warning('请填写完整')
      return
    }
    await createPrompt(newPrompt.value)
    ElMessage.success('已创建')
    createOpen.value = false
    newPrompt.value = { name: '', content: '', type: 'custom' }
    await load()
  }

  async function toggleEnabled(row: PromptItem) {
    const enabling = !row.enabled
    const action = enabling ? '启用' : '停用'
    const ok = await confirmAction({
      message: `确定要${action} Prompt「${row.name}」吗？`,
      confirmButtonText: action
    })
    if (!ok) return

    await setPromptEnabled(row.name, enabling)
    row.enabled = enabling
    ElMessage.success(row.enabled ? '已启用' : '已停用')
  }

  async function remove(row: PromptItem) {
    const ok = await confirmDelete(`确定删除 Prompt「${row.name}」吗？删除后不可恢复。`)
    if (!ok) return
    try {
      await deletePrompt(row.name)
      ElMessage.success('已删除')
      await load()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除失败'
      ElMessage.error(msg)
    }
  }

  onMounted(load)

  const ctx: PromptsAdminContext = {
    prompts,
    editVisible,
    previewVisible,
    previewing,
    createOpen,
    editing,
    newPrompt,
    loading,
    page,
    size,
    total,
    historyList,
    loadingHistory,
    historyPage,
    historySize,
    historyTotal,
    load,
    loadHistory,
    openEdit,
    openPreview,
    handleRollback,
    save,
    create,
    toggleEnabled,
    remove
  }

  provide(PROMPTS_ADMIN_KEY, ctx)
  return ctx
}

export function usePromptsAdmin(): PromptsAdminContext {
  const ctx = inject(PROMPTS_ADMIN_KEY)
  if (!ctx) {
    throw new Error('usePromptsAdmin() must be used within PromptsView')
  }
  return ctx
}
