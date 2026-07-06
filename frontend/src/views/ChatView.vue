<script setup lang="ts">
import { nextTick, onMounted, ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Cpu,
  Delete,
  Download,
  Fold,
  Memo,
  Plus,
  Promotion,
  Search,
  VideoPause,
  Box,
  FolderOpened
} from '@element-plus/icons-vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { fetchAvailableModels } from '@/api/chat'
import { fetchKnowledge, type KnowledgeItem } from '@/api/admin'
import { confirmDelete } from '@/utils/confirm'

const HISTORY_PREVIEW_COUNT = 8
const historyExpanded = ref(false)
const currentFilter = ref<'active' | 'archived'>('active')
const isBatchMode = ref(false)
const selectedIds = ref<string[]>([])

const HISTORY_COLLAPSED_KEY = 'agentone-chat-history-collapsed'
const historyCollapsed = ref(localStorage.getItem(HISTORY_COLLAPSED_KEY) === '1')

function toggleHistoryCollapsed(next?: boolean) {
  historyCollapsed.value = typeof next === 'boolean' ? next : !historyCollapsed.value
  try {
    localStorage.setItem(HISTORY_COLLAPSED_KEY, historyCollapsed.value ? '1' : '0')
  } catch { /* ignore */ }
}

const displayedConversations = computed(() => {
  return chatStore.filteredConversations.filter(c => {
    const archived = c.isArchived ?? false
    return currentFilter.value === 'archived' ? archived : !archived
  })
})

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

async function handleToggleArchive(conv: any) {
  const nextState = !conv.isArchived
  await chatStore.archiveConversation(conv.id, nextState)
}

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const inputText = ref('')
const messagesRef = ref<HTMLElement | null>(null)
const enableTools = ref(true)

interface ModelOption {
  name: string
  modelName: string
  provider: string
  isDefault: boolean
}

const models = ref<ModelOption[]>([])
const selectedModelId = ref('')
const kbs = ref<KnowledgeItem[]>([])
const selectedKbId = ref('')

async function loadKnowledge() {
  try {
    kbs.value = await fetchKnowledge()
  } catch (error) {
    // fallback
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

async function scrollToBottom(smooth = true) {
  await nextTick()
  const el = messagesRef.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  const convId = await chatStore.sendMessage(text, {
    enableTools: enableTools.value,
    modelId: selectedModelId.value || undefined,
    kbId: selectedKbId.value || undefined
  })
  if (convId && route.params.id !== convId) {
    await router.replace(`/chat/${convId}`)
  }
  await scrollToBottom()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (!chatStore.streaming) void handleSend()
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
  if (chatStore.creatingConversation || chatStore.streaming) return
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
  const nextId = await chatStore.removeConversation(id)
  if (route.params.id === id) {
    if (nextId) await router.replace(`/chat/${nextId}`)
    else await router.replace('/chat')
  }
  ElMessage.success('已删除')
}

watch(() => chatStore.messages.length, () => void scrollToBottom())

watch(
  () => chatStore.messages[chatStore.messages.length - 1]?.content,
  () => {
    if (chatStore.streaming) void scrollToBottom()
  }
)

watch(
  () => chatStore.streaming,
  async (val) => {
    if (!val) {
      await scrollToBottom()
      setTimeout(() => {
        void scrollToBottom()
      }, 350)
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
    if (!id && chatStore.currentId) {
      await router.replace(`/chat/${chatStore.currentId}`)
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

async function handleRegenerate(messageId: string) {
  await chatStore.regenerateMessage(messageId, {
    enableTools: enableTools.value,
    modelId: selectedModelId.value || undefined,
    kbId: selectedKbId.value || undefined
  })
  await scrollToBottom()
}

async function handleDeleteMessage(messageId: string) {
  const ok = await confirmDelete('确定删除此消息？')
  if (!ok) return
  await chatStore.removeMessage(messageId)
}

function handleExport() {
  void chatStore.exportCurrentConversation()
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
</script>

<template>
  <div class="chat-view ao-page" :class="{ 'chat-view--collapsed': historyCollapsed }">

    <!-- ===== 侧边栏 ===== -->
    <aside class="chat-sidebar" :class="{ 'chat-sidebar--collapsed': historyCollapsed }">
      <div class="sidebar-surface">

        <header class="sidebar-header">
          <div v-show="!historyCollapsed" class="sidebar-heading">对话历史</div>
          <div class="sidebar-header-actions">
            <button v-if="!historyCollapsed" type="button" class="sidebar-fold-btn" title="收起" @click="toggleHistoryCollapsed(true)">
              <el-icon><Fold /></el-icon>
            </button>
            <button
              type="button"
              class="sidebar-new-btn"
              title="新建对话"
              :disabled="chatStore.creatingConversation || chatStore.streaming"
              @click="handleNewChat"
            >
              <el-icon><Plus /></el-icon>
              <span v-show="!historyCollapsed">新对话</span>
            </button>
          </div>
        </header>

        <div v-show="!historyCollapsed" class="sidebar-body">
          <div class="sidebar-search-wrap">
            <el-icon class="sidebar-search-icon"><Search /></el-icon>
            <input v-model="chatStore.searchQuery" type="text" placeholder="搜索会话…" class="sidebar-search-input" />
          </div>

          <div class="sidebar-tabs">
            <div class="tabs-left">
              <button type="button" class="sidebar-tab" :class="{ active: currentFilter === 'active' }" @click="currentFilter = 'active'">活跃</button>
              <button type="button" class="sidebar-tab" :class="{ active: currentFilter === 'archived' }" @click="currentFilter = 'archived'">已归档</button>
            </div>
            <button
              type="button"
              class="sidebar-tab-batch-toggle"
              :class="{ active: isBatchMode }"
              @click="toggleBatchMode"
            >
              {{ isBatchMode ? '取消' : '批量' }}
            </button>
          </div>

          <div class="conv-list">
            <div v-if="chatStore.loadingConversations" class="conv-loading">
              <el-skeleton :rows="4" animated />
            </div>
            <template v-else-if="displayedConversations.length">
              <div v-for="conv in visibleConversations" :key="conv.id" class="conv-item-wrap">
                <div class="conv-item" :class="{ active: chatStore.currentId === conv.id, 'batch-padding': isBatchMode }" @click="isBatchMode ? null : selectChat(conv.id)">
                  <el-checkbox-group v-if="isBatchMode" v-model="selectedIds" class="batch-checkbox-wrap">
                    <el-checkbox :value="conv.id" @click.stop="" />
                  </el-checkbox-group>
                  <div class="conv-item-main">
                    <span class="conv-title">{{ conv.title }}</span>
                    <span class="conv-sub">{{ formatSessionTime(conv.updatedAt) }}</span>
                  </div>
                  <div class="conv-actions-overlay" v-if="!isBatchMode">
                    <button type="button" class="conv-action-btn" :title="conv.isArchived ? '取消归档' : '归档会话'" @click.stop="handleToggleArchive(conv)">
                      <el-icon :size="13"><FolderOpened v-if="conv.isArchived" /><Box v-else /></el-icon>
                    </button>
                    <button type="button" class="conv-action-btn conv-action-btn--delete" title="删除会话" @click.stop="handleDelete(conv.id, $event)">
                      <el-icon :size="13"><Delete /></el-icon>
                    </button>
                  </div>
                </div>
              </div>
              <button
                v-if="hiddenSessionCount > 0"
                type="button"
                class="history-load-more"
                @click="historyExpanded = !historyExpanded"
              >
                {{ historyExpanded ? '收起' : `更多（${hiddenSessionCount}）` }}
              </button>
            </template>
            <div v-else class="conv-empty">
              <p>暂无会话</p>
              <span>{{ currentFilter === 'archived' ? '无归档的会话记录' : '点击上方按钮开始新对话' }}</span>
            </div>
          </div>

          <div v-if="isBatchMode" class="batch-action-bar">
            <div class="batch-action-left">
              <button
                type="button"
                class="batch-pill-btn"
                :disabled="!displayedConversations.length"
                @click="toggleSelectAll"
              >
                {{ isAllSelected ? '取消全选' : '全选' }}
              </button>
              <span class="batch-selected-count">已选 {{ selectedIds.length }} 个</span>
            </div>
            <button
              type="button"
              class="batch-pill-btn batch-pill-btn--danger"
              :disabled="!selectedIds.length"
              @click="handleBatchDelete"
            >
              删除已选
            </button>
          </div>
        </div>

        <div v-show="historyCollapsed" class="sidebar-rail">
          <button type="button" class="sidebar-rail-btn" title="展开历史" @click="toggleHistoryCollapsed(false)">
            <el-icon><Memo /></el-icon>
          </button>
        </div>

      </div>
    </aside>

    <!-- ===== 主聊天区 ===== -->
    <section class="chat-main">

      <header class="chat-header">
        <div class="chat-header__left">
          <h2>{{ chatStore.currentConversation?.title || 'AI 对话' }}</h2>
          <span class="chat-header__meta">
            {{ models.find(m => m.name === selectedModelId)?.modelName || '默认模型' }} · {{ chatStore.totalTokens || 0 }} tokens
          </span>
        </div>
        <div class="chat-header__actions">
          <el-select v-model="selectedKbId" size="small" placeholder="挂载知识库" style="width: 130px;" clearable :disabled="chatStore.streaming">
            <el-option v-for="k in kbs" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
          <el-select v-model="selectedModelId" size="small" placeholder="选择模型" style="width: 130px;" :disabled="chatStore.streaming">
            <el-option v-for="m in models" :key="m.name" :label="m.modelName" :value="m.name" />
          </el-select>
          <el-tooltip content="导出 Markdown" placement="bottom">
            <el-button text circle :disabled="!chatStore.messages.length" @click="handleExport">
              <el-icon><Download /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="Agent 工作流监控" placement="bottom">
            <el-button text circle @click="goAgentMonitor">
              <el-icon><Cpu /></el-icon>
            </el-button>
          </el-tooltip>
          <el-switch v-model="enableTools" inline-prompt active-text="Tool" inactive-text="Tool" :disabled="chatStore.streaming" style="--el-switch-on-color: #4f46e5" />
        </div>
      </header>

      <div ref="messagesRef" class="chat-messages">
        <div v-if="chatStore.loadingMessages" class="messages-loading">
          <el-skeleton :rows="6" animated />
        </div>

        <div v-else-if="!chatStore.messages.length" class="fresh-state">
          <div class="empty-illustration">
            <div class="empty-orbit empty-orbit--a" />
            <div class="empty-orbit empty-orbit--b" />
            <div class="empty-core">
              <svg viewBox="0 0 64 64" width="44" height="44" fill="none">
                <circle cx="32" cy="32" r="28" stroke="url(#empty-grad)" stroke-width="2" opacity="0.4" />
                <path d="M22 38c0-5.5 4.5-12 10-12s10 6.5 10 12" stroke="#4f46e5" stroke-width="2.5" stroke-linecap="round" />
                <circle cx="26" cy="28" r="2.5" fill="#4f46e5" />
                <circle cx="38" cy="28" r="2.5" fill="#8b5cf6" />
                <defs>
                  <linearGradient id="empty-grad" x1="4" y1="4" x2="60" y2="60">
                    <stop stop-color="#4f46e5" />
                    <stop offset="1" stop-color="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
          <h3>今天想探索什么？</h3>
          <div class="fresh-state__chips">
            <button type="button" class="fresh-state__chip" @click="inputText = '帮我计算 123 × 456'">帮我计算 123 × 456</button>
            <button type="button" class="fresh-state__chip" @click="inputText = '用 Python 写一个快速排序'">用 Python 写一个快速排序</button>
            <button type="button" class="fresh-state__chip" @click="inputText = '解释 LangGraph 工作流'">解释 LangGraph 工作流</button>
          </div>
        </div>

        <template v-else>
          <ChatMessage
            v-for="msg in chatStore.messages"
            :key="msg.clientId || msg.id"
            :message="msg"
            :user-initial="userStore.displayName.charAt(0).toUpperCase()"
            :streaming="chatStore.streaming"
            @regenerate="handleRegenerate"
            @delete="handleDeleteMessage"
          />
        </template>
      </div>

      <footer class="chat-input-area">
        <div class="composer" :class="{ disabled: chatStore.streaming }">
          <textarea
            v-model="inputText"
            class="chat-textarea"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            rows="1"
            :disabled="chatStore.streaming"
            @keydown="handleKeydown"
          />
          <button v-if="chatStore.streaming" type="button" class="action-btn action-btn--stop" @click="handleStop">
            <el-icon><VideoPause /></el-icon>停止
          </button>
          <button v-else type="button" class="action-btn action-btn--send" :disabled="!inputText.trim()" @click="handleSend">
            <el-icon><Promotion /></el-icon>发送
          </button>
        </div>
        <p class="input-hint">AgentOne 可能会犯错，请核实重要信息。</p>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  align-items: stretch;
  height: calc(100vh - var(--ao-header-height) - 48px);
  min-height: 520px;
  max-width: 1400px;
}

/* ── 侧边栏 ── */
.chat-sidebar {
  flex: 0 0 260px;
  width: 260px;
  min-width: 0;
  transition: flex-basis 0.28s cubic-bezier(0.4,0,0.2,1), width 0.28s cubic-bezier(0.4,0,0.2,1);
}
.chat-sidebar--collapsed { flex-basis: 62px; width: 62px; }

.sidebar-surface {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-bg);
  box-shadow: 0 16px 40px var(--ao-panel-shadow);
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 12px 10px;
  border-bottom: 1px solid var(--ao-panel-border);
  flex-shrink: 0;
}
.chat-sidebar--collapsed .sidebar-header { flex-direction: column; justify-content: center; padding: 14px 10px; }

.sidebar-heading { font-weight: 700; font-size: 14px; color: var(--ao-text-primary); }

.sidebar-header-actions { display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0; }
.chat-sidebar--collapsed .sidebar-header-actions { flex-direction: column; }

.sidebar-fold-btn {
  width: 34px; height: 34px;
  border: 1px solid var(--ao-panel-border-strong);
  border-radius: 10px;
  background: var(--ao-panel-btn-bg);
  color: var(--ao-text-secondary);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s ease;
}
.sidebar-fold-btn:hover { color: var(--theme-primary); border-color: rgba(99,102,241,0.3); background: var(--theme-primary-muted); }

.sidebar-new-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 4px;
  border: none; border-radius: 999px; padding: 7px 14px;
  background: var(--theme-primary-gradient);
  color: #fff; font-size: 12px; font-weight: 600;
  cursor: pointer; flex-shrink: 0;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.chat-sidebar--collapsed .sidebar-new-btn { width: 34px; height: 34px; padding: 0; border-radius: 10px; }
.sidebar-new-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(79,70,229,0.24); }
.sidebar-new-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }

.sidebar-body { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.sidebar-search-wrap { position: relative; padding: 10px 10px 0; }
.sidebar-search-icon { position: absolute; left: 22px; top: 50%; transform: translateY(-20%); color: var(--ao-text-muted); font-size: 14px; }
.sidebar-search-input {
  width: 100%; height: 36px; padding: 0 12px 0 34px;
  border: 1px solid var(--ao-panel-border);
  border-radius: 999px; background: var(--ao-panel-input-bg);
  font-size: 13px; outline: none; transition: all 0.2s ease;
  box-sizing: border-box; color: var(--ao-text-primary);
}
.sidebar-search-input:focus { border-color: rgba(79,70,229,0.35); background: var(--ao-panel-bg); box-shadow: 0 0 0 3px rgba(79,70,229,0.08); }

.sidebar-tabs { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px 4px; gap: 8px; }
.tabs-left { display: flex; gap: 6px; }
.sidebar-tab {
  background: var(--ao-panel-btn-bg);
  border: 1px solid var(--ao-panel-border);
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  cursor: pointer;
  padding: 4px 14px;
  border-radius: 999px;
  transition: all 0.2s ease;
}
.sidebar-tab:hover {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 30%, transparent);
  background: var(--theme-primary-muted);
}
.sidebar-tab.active {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}
.sidebar-tab-batch-toggle {
  background: var(--ao-panel-btn-bg);
  border: 1px solid var(--ao-panel-border);
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  cursor: pointer;
  padding: 4px 14px;
  border-radius: 999px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.sidebar-tab-batch-toggle:hover,
.sidebar-tab-batch-toggle.active {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}

.conv-list { flex: 1; overflow-y: auto; padding: 4px 10px 10px; scrollbar-width: none; }
.conv-list::-webkit-scrollbar { display: none; }

.conv-loading, .conv-empty { padding: 24px 12px; text-align: center; color: var(--ao-text-muted); font-size: 13px; }
.conv-empty p { margin: 0 0 4px; font-weight: 600; }
.conv-empty span { font-size: 11px; }

.history-load-more {
  width: 100%;
  margin-top: 4px;
  padding: 8px 10px;
  border: 1px dashed var(--ao-panel-border);
  border-radius: 12px;
  background: transparent;
  color: var(--ao-text-muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.history-load-more:hover {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}

.conv-item-wrap { margin-bottom: 6px; }
.conv-item {
  position: relative; display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 36px 9px 10px;
  border: 1px solid var(--ao-conv-border);
  border-radius: 14px; background: var(--ao-conv-bg);
  overflow: hidden; cursor: pointer; transition: all 0.2s ease; box-sizing: border-box;
}
.conv-item:hover, .conv-item.active {
  border-color: rgba(99,102,241,0.35);
  background: var(--ao-conv-active-bg);
  box-shadow: 0 8px 20px rgba(79,70,229,0.08);
}
.conv-item.batch-padding { padding-left: 36px; }

.batch-checkbox-wrap { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); }

.conv-item-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.conv-title { display: block; font-size: 13px; font-weight: 700; color: var(--ao-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conv-sub { font-size: 11px; color: var(--ao-text-muted); }

.conv-actions-overlay {
  position: absolute; right: 0; top: 0; bottom: 0;
  display: flex; align-items: center; gap: 4px;
  padding-right: 8px; padding-left: 20px;
  background: var(--ao-conv-overlay-bg);
  border-top-right-radius: 14px; border-bottom-right-radius: 14px;
  opacity: 0; transition: opacity 0.18s ease;
}
.conv-item:hover .conv-actions-overlay, .conv-item.active .conv-actions-overlay { opacity: 1; }

.conv-action-btn {
  width: 22px; height: 22px; border: none; border-radius: 999px;
  background: var(--ao-conv-action-bg); color: var(--ao-text-muted);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.18s ease;
}
.conv-action-btn:hover { color: var(--theme-primary); background: var(--ao-panel-bg); }
.conv-action-btn--delete:hover { color: #ef4444; }

.batch-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-top: 1px solid var(--ao-panel-border);
  flex-shrink: 0;
}
.batch-action-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.batch-pill-btn {
  height: 28px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-btn-bg);
  color: var(--ao-text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.batch-pill-btn:hover:not(:disabled) {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}
.batch-pill-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.batch-pill-btn--danger {
  border-color: rgba(239, 68, 68, 0.35);
  color: #ef4444;
  background: rgba(239, 68, 68, 0.06);
}
.batch-pill-btn--danger:hover:not(:disabled) {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}
.batch-selected-count { font-size: 12px; font-weight: 600; color: var(--ao-text-muted); }

.sidebar-rail { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 12px 10px 16px; flex: 1; }
.sidebar-rail-btn {
  width: 40px; height: 40px;
  border: 1px solid var(--ao-panel-border-strong);
  border-radius: 14px; background: var(--ao-panel-btn-bg); color: var(--theme-primary);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s ease;
}
.sidebar-rail-btn:hover { border-color: rgba(99,102,241,0.32); background: var(--theme-primary-muted); }

/* ── 主聊天区 ── */
.chat-main {
  flex: 1; min-width: 0; display: flex; flex-direction: column;
  border-radius: 24px; border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-bg); box-shadow: 0 16px 40px var(--ao-panel-shadow);
  overflow: hidden; position: relative; margin-left: 12px;
  transition: margin-left 0.28s cubic-bezier(0.4,0,0.2,1);
}
.chat-view--collapsed .chat-main { margin-left: 10px; }

.chat-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 14px 20px; border-bottom: 1px solid var(--ao-panel-border);
  flex-shrink: 0; background: var(--ao-panel-header-bg);
}
.chat-header__left { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.chat-header h2 { margin: 0; font-size: 15px; font-weight: 700; color: var(--ao-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-header__meta { font-size: 12px; color: var(--ao-text-muted); }
.chat-header__actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px 20px 12px;
  background: var(--ao-messages-bg);
  scrollbar-width: thin; scrollbar-color: rgba(148,163,184,0.5) transparent;
}
.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.45); border-radius: 999px; }

.messages-loading { max-width: 600px; margin: 0 auto; }

/* 空状态 */
.fresh-state { min-height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 32px 24px; }

.empty-illustration { position: relative; width: 140px; height: 140px; margin-bottom: 24px; }
.empty-orbit { position: absolute; border-radius: 50%; border: 1.5px dashed rgba(99,102,241,0.25); }
.empty-orbit--a { inset: 0; animation: orbit-spin 20s linear infinite; }
.empty-orbit--b { inset: 16px; animation: orbit-spin 14s linear infinite reverse; }
.empty-core { position: absolute; inset: 32px; border-radius: 50%; background: var(--ao-panel-btn-bg); display: flex; align-items: center; justify-content: center; box-shadow: 0 12px 40px rgba(79,70,229,0.12); }
@keyframes orbit-spin { to { transform: rotate(360deg); } }

.fresh-state h3 { margin: 0; font-size: 28px; font-weight: 800; color: var(--ao-text-primary); line-height: 1.25; }
.fresh-state__chips { margin-top: 28px; display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }
.fresh-state__chip { border: 1px solid var(--ao-chip-border); background: var(--ao-panel-bg); color: var(--ao-text-secondary); border-radius: 999px; padding: 10px 20px; font-size: 13px; cursor: pointer; transition: all 0.2s ease; }
.fresh-state__chip:hover { border-color: rgba(99,102,241,0.3); color: var(--theme-primary); background: var(--theme-primary-muted); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(79,70,229,0.1); }

/* 输入区 */
.chat-input-area { padding: 12px 16px 16px; border-top: 1px solid var(--ao-panel-border); background: var(--ao-panel-footer-bg); flex-shrink: 0; }
.composer { display: flex; align-items: flex-end; gap: 10px; padding: 8px 10px 8px 18px; background: var(--ao-composer-bg); border: 1px solid var(--ao-composer-border); border-radius: 24px; transition: all 0.22s ease; }
.composer:focus-within { background: var(--ao-panel-bg); border-color: rgba(79,70,229,0.4); box-shadow: 0 0 0 3px rgba(79,70,229,0.1); }
.composer.disabled { opacity: 0.85; }
.chat-textarea { flex: 1; border: none; outline: none; resize: none; background: transparent; font-size: 14px; line-height: 1.5; padding: 8px 0; max-height: 120px; font-family: inherit; color: var(--ao-text-primary); }
.chat-textarea::placeholder { color: var(--ao-text-muted); }

.action-btn { display: flex; align-items: center; gap: 6px; height: 36px; padding: 0 18px; border: none; border-radius: 999px; font-size: 13px; font-weight: 700; cursor: pointer; flex-shrink: 0; transition: all 0.2s ease; margin-bottom: 2px; }
.action-btn--send {
  background: var(--ao-chat-send-gradient) !important;
  color: #fff !important;
  box-shadow: var(--ao-chat-send-shadow);
}
.action-btn--send:disabled {
  cursor: not-allowed;
  box-shadow: none;
  background: var(--ao-chat-send-gradient-disabled) !important;
  color: #fff !important;
  opacity: 1;
}
.action-btn--send:not(:disabled):hover {
  filter: brightness(1.06);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.42);
  transform: translateY(-1px);
}
.action-btn--stop {
  background: rgba(239, 68, 68, 0.09) !important;
  color: #ef4444 !important;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.input-hint { margin: 8px 0 0; text-align: center; font-size: 11px; color: var(--ao-text-muted); }

@media (max-width: 860px) {
  .chat-view { flex-direction: column; height: auto; min-height: auto; }
  .chat-sidebar, .chat-sidebar--collapsed { flex-basis: auto; width: 100%; }
  .chat-main { margin-left: 0; margin-top: 10px; min-height: 560px; }
}
</style>
