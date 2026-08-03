import { computed, inject, nextTick, onMounted, provide, ref, watch, type InjectionKey, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { fetchAvailableModels } from '@/api/chat'
import { fetchAllKnowledge, uploadFile, type KnowledgeItem } from '@/api/admin'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import type { AgentMode, ConversationSummary, KbMode, ThinkingLevel } from '@/types'

const HISTORY_PREVIEW_COUNT = 8
const HISTORY_COLLAPSED_KEY = 'agentone-chat-history-collapsed'
const KB_MODE_KEY = 'agentone-kb-mode'
const KB_IDS_KEY = 'agentone-selected-kb-ids'
const AGENT_MODE_KEY = 'agentone-agent-mode'
const THINKING_LEVEL_KEY = 'agentone-thinking-level'
const MAX_MOUNTED_KBS = 10

function loadStoredAgentMode(): AgentMode {
  const raw = localStorage.getItem(AGENT_MODE_KEY)
  return raw === 'multi' || raw === 'plan' ? raw : 'standard'
}

function loadStoredThinkingLevel(): ThinkingLevel {
  const raw = localStorage.getItem(THINKING_LEVEL_KEY)
  return raw === 'fast' || raw === 'extended' ? raw : 'standard'
}

function loadStoredKbIds(): string[] {
  try {
    const raw = localStorage.getItem(KB_IDS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter((id): id is string => typeof id === 'string' && Boolean(id))
  } catch {
    return []
  }
}

interface ModelOption {
  name: string
  modelName: string
  provider: string
  isDefault: boolean
}

export interface ChatViewContext {
  chatStore: ReturnType<typeof useChatStore>
  userStore: ReturnType<typeof useUserStore>
  inputText: Ref<string>
  messagesRef: Ref<HTMLElement | null>
  enableTools: Ref<boolean>
  agentMode: Ref<AgentMode>
  setAgentMode: (mode: AgentMode) => void
  models: Ref<ModelOption[]>
  selectedModelId: Ref<string>
  thinkingLevel: Ref<ThinkingLevel>
  kbs: Ref<KnowledgeItem[]>
  selectedKbIds: Ref<string[]>
  kbRetrieveOnly: Ref<boolean>
  setKbRetrieveOnly: (value: boolean) => void
  historyCollapsed: Ref<boolean>
  historyExpanded: Ref<boolean>
  currentFilter: Ref<'active' | 'archived'>
  isBatchMode: Ref<boolean>
  selectedIds: Ref<string[]>
  displayedConversations: Ref<ConversationSummary[]>
  visibleConversations: Ref<ConversationSummary[]>
  hiddenSessionCount: Ref<number>
  isAllSelected: Ref<boolean>
  toggleHistoryCollapsed: (next?: boolean) => void
  toggleBatchMode: () => void
  toggleSelectAll: () => void
  handleBatchDelete: () => Promise<void>
  handleToggleArchive: (conv: ConversationSummary) => Promise<void>
  handleSend: () => Promise<void>
  handleKeydown: (e: KeyboardEvent) => void
  handleStop: () => void
  goAgentMonitor: () => void
  handleNewChat: () => Promise<void>
  selectChat: (id: string) => Promise<void>
  handleDelete: (id: string, e: Event) => Promise<void>
  handleRegenerate: (messageId: string) => Promise<void>
  handleDeleteMessage: (messageId: string) => Promise<void>
  handleExport: () => void
  formatSessionTime: (value: string) => string
  attachedFile: Ref<{ id: string; name: string; url?: string; isImage?: boolean } | null>
  uploadingFile: Ref<boolean>
  handleUploadChatFile: (file: File) => Promise<void>
  clearAttachment: () => void
}

export const CHAT_VIEW_KEY: InjectionKey<ChatViewContext> = Symbol('chatView')

export function useChatViewProvider(): ChatViewContext {
  const historyExpanded = ref(false)
  const currentFilter = ref<'active' | 'archived'>('active')
  const isBatchMode = ref(false)
  const selectedIds = ref<string[]>([])
  const historyCollapsed = ref(localStorage.getItem(HISTORY_COLLAPSED_KEY) === '1')

  const route = useRoute()
  const router = useRouter()
  const chatStore = useChatStore()
  const userStore = useUserStore()

  const DRAFT_KEY_PREFIX = 'agentone-chat-draft-'
  function getDraftKey(convId: string | null): string {
    return `${DRAFT_KEY_PREFIX}${convId || 'new'}`
  }
  function loadDraft(convId: string | null): string {
    try {
      return sessionStorage.getItem(getDraftKey(convId)) || ''
    } catch {
      return ''
    }
  }
  function saveDraft(convId: string | null, text: string) {
    try {
      const key = getDraftKey(convId)
      if (text) {
        sessionStorage.setItem(key, text)
      } else {
        sessionStorage.removeItem(key)
      }
    } catch {
      /* ignore */
    }
  }

  const inputText = ref(loadDraft(chatStore.currentId))
  const messagesRef = ref<HTMLElement | null>(null)
  const enableTools = ref(true)
  const agentMode = ref<AgentMode>(loadStoredAgentMode())

  // 会话切换时自动保存旧草稿，加载新草稿
  watch(
    () => chatStore.currentId,
    (newId, oldId) => {
      if (oldId !== newId) {
        saveDraft(oldId, inputText.value)
        inputText.value = loadDraft(newId)
      }
    }
  )

  // 实时同步当前输入框文本到草稿
  watch(inputText, (val) => {
    saveDraft(chatStore.currentId, val)
  })
  const models = ref<ModelOption[]>([])
  const selectedModelId = ref('')
  const thinkingLevel = ref<ThinkingLevel>(loadStoredThinkingLevel())
  const kbs = ref<KnowledgeItem[]>([])
  const selectedKbIds = ref<string[]>(loadStoredKbIds())
  const kbRetrieveOnly = ref(localStorage.getItem(KB_MODE_KEY) === 'retrieve')
  const attachedFile = ref<{ id: string; name: string; url?: string; isImage?: boolean } | null>(null)
  const uploadingFile = ref(false)

  async function handleUploadChatFile(file: File) {
    uploadingFile.value = true
    try {
      const res = await uploadFile(file)
      const fileName = res.name || file.name || 'unnamed'
      const ext = fileName.toLowerCase()
      const isImg = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg'].some((e) => ext.endsWith(e))
      const token = userStore.token || localStorage.getItem('token') || ''
      const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : ''
      const downloadUrl = `/api/v1/files/${res.id}/download${tokenQuery}`
      attachedFile.value = {
        id: res.id,
        name: fileName,
        url: downloadUrl,
        isImage: isImg
      }
      ElMessage.success(isImg ? '图片已上传关联' : '文件已上传关联')
    } catch {
      ElMessage.error('文件上传失败')
    } finally {
      uploadingFile.value = false
    }
  }

  function clearAttachment() {
    attachedFile.value = null
  }

  function resolveKbMode(): KbMode | undefined {
    if (!selectedKbIds.value.length) return undefined
    return kbRetrieveOnly.value ? 'retrieve' : 'generate'
  }

  function setKbRetrieveOnly(value: boolean) {
    kbRetrieveOnly.value = value
    try {
      localStorage.setItem(KB_MODE_KEY, value ? 'retrieve' : 'generate')
    } catch {
      /* ignore */
    }
  }

  function setAgentMode(mode: AgentMode) {
    agentMode.value = mode
    try {
      localStorage.setItem(AGENT_MODE_KEY, mode)
    } catch {
      /* ignore */
    }
  }

  /** 将当前 Agent 模式映射为请求参数（standard 不传，保持默认路径） */
  function resolveAgentModeOptions() {
    return {
      multiAgent: agentMode.value === 'multi' || undefined,
      planExecute: agentMode.value === 'plan' || undefined,
      thinkingLevel: thinkingLevel.value
    }
  }

  // 扩展思考档位持久化（v-model 直接绑定到 ref，watch 落盘）
  watch(thinkingLevel, (level) => {
    try {
      localStorage.setItem(THINKING_LEVEL_KEY, level)
    } catch {
      /* ignore */
    }
  })

  let kbClearGuard = false

  watch(
    selectedKbIds,
    async (newVal, oldVal) => {
      if (kbClearGuard) return
      const prev = [...(oldVal ?? [])]
      // 一次从 2+ 个变为 0 只能是点右侧「全部清空」，单个 tag 删除不会触发
      if (newVal.length === 0 && prev.length >= 2) {
        kbClearGuard = true
        selectedKbIds.value = prev
        const ok = await confirmDelete({
          title: '清空确认',
          message: `确定清空已挂载的 ${prev.length} 个知识库吗？`,
          confirmButtonText: '清空'
        })
        if (ok) {
          selectedKbIds.value = []
        }
        await nextTick()
        kbClearGuard = false
      }
    },
    { deep: true }
  )

  function toggleHistoryCollapsed(next?: boolean) {
    historyCollapsed.value = typeof next === 'boolean' ? next : !historyCollapsed.value
    try {
      localStorage.setItem(HISTORY_COLLAPSED_KEY, historyCollapsed.value ? '1' : '0')
    } catch {
      /* ignore */
    }
  }

  const displayedConversations = computed(() =>
    chatStore.filteredConversations.filter((c) => {
      const archived = c.isArchived ?? false
      return currentFilter.value === 'archived' ? archived : !archived
    })
  )

  const visibleConversations = computed(() =>
    historyExpanded.value
      ? displayedConversations.value
      : displayedConversations.value.slice(0, HISTORY_PREVIEW_COUNT)
  )

  const hiddenSessionCount = computed(() =>
    Math.max(0, displayedConversations.value.length - HISTORY_PREVIEW_COUNT)
  )

  const isAllSelected = computed(() => {
    const ids = displayedConversations.value.map((c) => c.id)
    return ids.length > 0 && ids.every((id) => selectedIds.value.includes(id))
  })

  function toggleBatchMode() {
    isBatchMode.value = !isBatchMode.value
    selectedIds.value = []
  }

  function toggleSelectAll() {
    if (isAllSelected.value) {
      selectedIds.value = []
      return
    }
    selectedIds.value = displayedConversations.value.map((c) => c.id)
  }

  async function handleBatchDelete() {
    if (!selectedIds.value.length) return
    const ok = await confirmDelete({
      title: '批量删除确认',
      message: `确认批量删除这 ${selectedIds.value.length} 个会话吗？`
    })
    if (!ok) return
    const deletedCurrent = Boolean(chatStore.currentId && selectedIds.value.includes(chatStore.currentId))
    await chatStore.removeConversationsBatch(selectedIds.value)
    isBatchMode.value = false
    selectedIds.value = []
    if (deletedCurrent && chatStore.currentId) {
      await router.replace(`/chat/${chatStore.currentId}`)
    }
  }

  async function handleToggleArchive(conv: ConversationSummary) {
    const isArchiving = !conv.isArchived
    const title = isArchiving ? '归档对话' : '恢复对话'
    const message = isArchiving
      ? `确认归档对话「${conv.title || '未命名'}」吗？归档后可在“已归档”列表中查看。`
      : `确认将对话「${conv.title || '未命名'}」重新恢复到活跃列表中吗？`
    const confirmButtonText = isArchiving ? '归档' : '恢复'

    const ok = await confirmAction({
      title,
      message,
      confirmButtonText,
      cancelButtonText: '取消',
      type: 'info'
    })
    if (!ok) return

    try {
      await chatStore.archiveConversation(conv.id, isArchiving)
      ElMessage.success(isArchiving ? '已归档对话' : '已恢复对话')
    } catch {
      ElMessage.error(isArchiving ? '归档失败' : '恢复失败')
    }
  }

  async function loadKnowledge() {
    try {
      kbs.value = await fetchAllKnowledge()
      const valid = new Set(kbs.value.map((k) => k.id))
      selectedKbIds.value = selectedKbIds.value.filter((id) => valid.has(id))
    } catch {
      /* ignore */
    }
  }

  async function loadModels() {
    try {
      const list = await fetchAvailableModels()
      models.value = list
      const def = list.find((m) => m.isDefault) || list[0]
      selectedModelId.value = def?.name || ''
    } catch {
      models.value = []
    }
  }

  const userScrolledUp = ref(false)

  function handleWheel(e: WheelEvent) {
    // 当用户向上滚动滚轮/触摸板 (deltaY < -2)，瞬间识别向上翻看意图，立刻解除跟随锁定
    if (e.deltaY < -2) {
      userScrolledUp.value = true
    }
  }

  function handleContainerScroll() {
    const el = messagesRef.value
    if (!el) return
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    if (distanceToBottom > 60) {
      userScrolledUp.value = true
    } else if (distanceToBottom < 30) {
      userScrolledUp.value = false
    }
  }

  watch(messagesRef, (el, oldEl) => {
    if (oldEl) {
      oldEl.removeEventListener('scroll', handleContainerScroll)
      oldEl.removeEventListener('wheel', handleWheel)
    }
    if (el) {
      el.addEventListener('scroll', handleContainerScroll, { passive: true })
      el.addEventListener('wheel', handleWheel, { passive: true })
    }
  }, { immediate: true })

  async function scrollToBottom(smooth = true, force = true) {
    const el = messagesRef.value
    if (!el) return
    await nextTick()
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    const isNearBottom = distanceToBottom < 60

    if (force) {
      userScrolledUp.value = false
    }

    if (force || (!userScrolledUp.value && isNearBottom)) {
      // 流式输出时使用 'auto' (即时底置) 防止平滑过渡动画延时积累导致追不上打字速度
      const behavior = (smooth && !chatStore.streaming) ? 'smooth' : 'auto'
      el.scrollTo({ top: el.scrollHeight, behavior })
    }
  }

  async function handleSend() {
    let text = inputText.value.trim()
    if (!text && !attachedFile.value) return

    if (chatStore.streaming) {
      chatStore.abortStream()
    }

    if (!text && attachedFile.value) {
      if (attachedFile.value.isImage && attachedFile.value.url) {
        text = `![${attachedFile.value.name}](${attachedFile.value.url})`
      } else {
        text = `请帮我读取并分析刚才上传的文件「${attachedFile.value.name}」。`
      }
    } else if (attachedFile.value) {
      if (attachedFile.value.isImage && attachedFile.value.url) {
        text = `![${attachedFile.value.name}](${attachedFile.value.url})\n\n${text}`
      } else {
        text = `[已上传关联文件: ${attachedFile.value.name}]\n\n${text}`
      }
    }
    inputText.value = ''
    attachedFile.value = null

    const convId = await chatStore.sendMessage(text, {
      enableTools: enableTools.value,
      modelId: selectedModelId.value || undefined,
      kbIds: selectedKbIds.value.length ? [...selectedKbIds.value] : undefined,
      kbMode: resolveKbMode(),
      ...resolveAgentModeOptions()
    })
    if (convId && route.params.id !== convId) {
      await router.replace(`/chat/${convId}`)
    }
    await scrollToBottom()
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  function handleStop() {
    chatStore.abortStream()
  }

  function goAgentMonitor() {
    if (chatStore.currentId) {
      void router.push({ path: '/agent', query: { conversationId: chatStore.currentId } })
    } else {
      void router.push('/agent')
    }
  }

  async function handleNewChat() {
    if (chatStore.creatingConversation) return
    const conv = await chatStore.startNewChat()
    if (route.params.id !== conv.id) {
      await router.push(`/chat/${conv.id}`)
    }
  }

  async function selectChat(id: string) {
    await chatStore.selectConversation(id)
    await router.push(`/chat/${id}`)
    await scrollToBottom(false)
  }

  async function handleDelete(id: string, e: Event) {
    e.preventDefault()
    e.stopPropagation()
    const conv = chatStore.conversations.find((c) => c.id === id)
    const ok = await confirmDelete({
      title: '删除对话',
      message: `确认删除对话「${conv?.title || '未命名'}」吗？`
    })
    if (!ok) return
    try {
      const nextId = await chatStore.removeConversation(id)
      if (route.params.id === id) {
        if (nextId) await router.replace(`/chat/${nextId}`)
        else await router.replace('/chat')
      }
      ElMessage.success('已删除')
    } catch {
      /* error already shown */
    }
  }

  async function handleRegenerate(messageId: string) {
    await chatStore.regenerateMessage(messageId, {
      enableTools: enableTools.value,
      modelId: selectedModelId.value || undefined,
      kbIds: selectedKbIds.value.length ? [...selectedKbIds.value] : undefined,
      kbMode: resolveKbMode(),
      ...resolveAgentModeOptions()
    })
    await scrollToBottom()
  }

  async function handleDeleteMessage(messageId: string) {
    const ok = await confirmDelete('确定删除此消息？')
    if (!ok) return
    await chatStore.removeMessage(messageId)
  }

  async function handleExport() {
    const title = chatStore.currentConversation?.title || '此对话'
    const ok = await confirmAction({
      title: '导出 Markdown 确认',
      message: `确认导出对话「${title}」的完整聊天记录为 Markdown 文件吗？`,
      confirmButtonText: '导出',
      cancelButtonText: '取消',
      type: 'info'
    })
    if (!ok) return

    await chatStore.exportCurrentConversation()
  }

  function formatSessionTime(value: string) {
    if (!value) return ''
    const date = new Date(value)
    if (isNaN(date.getTime())) return value
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${year}/${month}/${day} ${hour}:${minute}`
  }

  watch(
    selectedKbIds,
    (ids) => {
      try {
        localStorage.setItem(KB_IDS_KEY, JSON.stringify(ids.slice(0, MAX_MOUNTED_KBS)))
      } catch {
        /* ignore */
      }
    },
    { deep: true }
  )

  watch(() => chatStore.messages.length, () => void scrollToBottom())

  watch(
    () => chatStore.messages[chatStore.messages.length - 1]?.content,
    () => {
      if (chatStore.streaming) void scrollToBottom(false, false)
    }
  )

  watch(
    () => chatStore.streaming,
    async (val) => {
      if (val) {
        userScrolledUp.value = false
      } else {
        await scrollToBottom(true, false)
        setTimeout(() => {
          void scrollToBottom(true, false)
        }, 200)
      }
    }
  )

  watch(
    () => route.params.id,
    async (id) => {
      if (!chatStore.initialized) return
      if (typeof id === 'string' && id && chatStore.currentId !== id) {
        await chatStore.selectConversation(id)
        await scrollToBottom(false)
        return
      }
      if (!id) {
        const conv = await chatStore.startNewChat()
        if (route.params.id !== conv.id) {
          await router.replace(`/chat/${conv.id}`)
        }
        await scrollToBottom(false)
        return
      }
    }
  )

  onMounted(async () => {
    await Promise.all([loadModels(), loadKnowledge()])
    try {
      const routeId = typeof route.params.id === 'string' ? route.params.id : null
      await chatStore.ensureInitialized(routeId)
    } catch {
      ElMessage.error('加载对话失败')
    }

    if (chatStore.currentId && route.params.id !== chatStore.currentId) {
      await router.replace(`/chat/${chatStore.currentId}`)
    }
    await scrollToBottom(false)
  })

  const ctx: ChatViewContext = {
    chatStore,
    userStore,
    inputText,
    messagesRef,
    enableTools,
    agentMode,
    setAgentMode,
    models,
    selectedModelId,
    thinkingLevel,
    kbs,
    selectedKbIds,
    kbRetrieveOnly,
    setKbRetrieveOnly,
    historyCollapsed,
    historyExpanded,
    currentFilter,
    isBatchMode,
    selectedIds,
    displayedConversations,
    visibleConversations,
    hiddenSessionCount,
    isAllSelected,
    toggleHistoryCollapsed,
    toggleBatchMode,
    toggleSelectAll,
    handleBatchDelete,
    handleToggleArchive,
    handleSend,
    handleKeydown,
    handleStop,
    goAgentMonitor,
    handleNewChat,
    selectChat,
    handleDelete,
    handleRegenerate,
    handleDeleteMessage,
    handleExport,
    formatSessionTime,
    attachedFile,
    uploadingFile,
    handleUploadChatFile,
    clearAttachment
  }

  provide(CHAT_VIEW_KEY, ctx)
  return ctx
}

export function useChatView(): ChatViewContext {
  const ctx = inject(CHAT_VIEW_KEY)
  if (!ctx) {
    throw new Error('useChatView() must be used within ChatView')
  }
  return ctx
}
