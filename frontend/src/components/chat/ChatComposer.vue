<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { Close, Document, Loading, Paperclip, Promotion, VideoPause } from '@element-plus/icons-vue'
import { useChatView } from '@/composables/useChatView'
import ModelSelectorPopover from './ModelSelectorPopover.vue'
import VoiceLanguageButton from './VoiceLanguageButton.vue'

const {
  chatStore,
  inputText,
  models,
  selectedModelId,
  thinkingLevel,
  handleSend,
  handleKeydown,
  handleStop,
  attachedFile,
  uploadingFile,
  handleUploadChatFile,
  clearAttachment
} = useChatView()

const fileInputRef = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isMultiline = ref(false)

function triggerFileSelect() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  void handleUploadChatFile(file)
  target.value = ''
}

function onVoiceUpdateText(text: string) {
  inputText.value = text
}

function checkMultiline() {
  const val = inputText.value || ''
  if (!val) {
    isMultiline.value = false
    return
  }
  if (val.includes('\n')) {
    isMultiline.value = true
    return
  }
  const el = textareaRef.value
  if (el) {
    // 高度超过单行 (42px) 即判定为多行自动折行
    isMultiline.value = el.scrollHeight > 42
  } else {
    isMultiline.value = val.length > 55
  }
}

function adjustTextareaHeight() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  const minH = isMultiline.value ? 40 : 36
  const nextH = Math.min(Math.max(el.scrollHeight, minH), 220)
  el.style.height = `${nextH}px`
}

function onInput() {
  checkMultiline()
  adjustTextareaHeight()
}

watch(
  inputText,
  () => {
    nextTick(() => {
      checkMultiline()
      adjustTextareaHeight()
    })
  },
  { immediate: true }
)
</script>

<template>
  <footer class="chat-input-area">
    <!-- Attached file preview chip -->
    <div v-if="attachedFile" class="attached-file-chip">
      <img v-if="attachedFile.isImage && attachedFile.url" :src="attachedFile.url" class="chip-image-thumb" />
      <el-icon v-else class="file-icon"><Document /></el-icon>
      <span class="file-name">{{ attachedFile.name }}</span>
      <el-button class="remove-btn" type="text" :icon="Close" circle @click="clearAttachment" />
    </div>

    <!-- 动态模式：无文字/单行时为经典单行胶囊框，多行时展开为大卡片 -->
    <div class="composer" :class="{ 'is-expanded': isMultiline }">
      <!-- 模式 1：未超长/单行文字（保持 100% 原样单行胶囊边框） -->
      <template v-if="!isMultiline">
        <button
          type="button"
          class="composer-btn composer-btn--attach"
          title="上传文件/图片/音视频 (PDF, Word, 图片, MP3, MP4 等，可对其提问)"
          :disabled="uploadingFile"
          @click="triggerFileSelect"
        >
          <el-icon v-if="uploadingFile" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><Paperclip /></el-icon>
        </button>
        <input
          ref="fileInputRef"
          type="file"
          style="display: none"
          accept=".pdf,.docx,.doc,.txt,.md,.markdown,.png,.jpg,.jpeg,.webp,.gif,.bmp,.svg,.xlsx,.xls,.csv,.mp3,.wav,.m4a,.flac,.ogg,.aac,.mp4,.avi,.mov,.mkv,.webm,.flv"
          @change="onFileChange"
        />

        <textarea
          ref="textareaRef"
          v-model="inputText"
          class="chat-textarea chat-textarea--single"
          placeholder="输入消息，Enter 发送，Shift+Enter 换行"
          rows="1"
          @keydown="handleKeydown"
          @input="onInput"
        />

        <div class="composer-right-actions">
          <ModelSelectorPopover
            v-model="selectedModelId"
            v-model:thinking-level="thinkingLevel"
            :models="models"
            :disabled="chatStore.streaming"
          />

          <VoiceLanguageButton :current-text="inputText" @update-text="onVoiceUpdateText" />

          <button v-if="chatStore.streaming" type="button" class="action-btn action-btn--stop" @click="handleStop">
            <el-icon class="stop-icon"><VideoPause /></el-icon>
            <span>停止</span>
          </button>

          <Transition name="scale-send">
            <button
              v-if="!chatStore.streaming && (inputText.trim() || attachedFile)"
              type="button"
              class="action-btn action-btn--send"
              title="发送消息"
              @click="handleSend"
            >
              <el-icon><Promotion /></el-icon>
            </button>
          </Transition>
        </div>
      </template>

      <!-- 模式 2：文字多行展开（模仿图 1 大卡片边框结构，不改动 Logo） -->
      <template v-else>
        <div class="composer-top-row">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            class="chat-textarea chat-textarea--multi"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            rows="2"
            @keydown="handleKeydown"
            @input="onInput"
          />
        </div>

        <div class="composer-toolbar-row">
          <div class="toolbar-left">
            <button
              type="button"
              class="composer-btn composer-btn--attach"
              title="上传文件/图片/音视频 (PDF, Word, 图片, MP3, MP4 等，可对其提问)"
              :disabled="uploadingFile"
              @click="triggerFileSelect"
            >
              <el-icon v-if="uploadingFile" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Paperclip /></el-icon>
            </button>
            <input
              ref="fileInputRef"
              type="file"
              style="display: none"
              accept=".pdf,.docx,.doc,.txt,.md,.markdown,.png,.jpg,.jpeg,.webp,.gif,.bmp,.svg,.xlsx,.xls,.csv,.mp3,.wav,.m4a,.flac,.ogg,.aac,.mp4,.avi,.mov,.mkv,.webm,.flv"
              @change="onFileChange"
            />
          </div>

          <div class="toolbar-right">
            <ModelSelectorPopover
              v-model="selectedModelId"
              v-model:thinking-level="thinkingLevel"
              :models="models"
              :disabled="chatStore.streaming"
            />

            <VoiceLanguageButton :current-text="inputText" @update-text="onVoiceUpdateText" />

            <button v-if="chatStore.streaming" type="button" class="action-btn action-btn--stop" @click="handleStop">
              <el-icon class="stop-icon"><VideoPause /></el-icon>
              <span>停止</span>
            </button>

            <Transition name="scale-send">
              <button
                v-if="!chatStore.streaming && (inputText.trim() || attachedFile)"
                type="button"
                class="action-btn action-btn--send"
                title="发送消息"
                @click="handleSend"
              >
                <el-icon><Promotion /></el-icon>
              </button>
            </Transition>
          </div>
        </div>
      </template>
    </div>

    <p class="input-hint">AgentOne 可能会犯错，请核实重要信息。</p>
  </footer>
</template>

<style scoped>
.chat-input-area {
  padding: 10px 14px 6px;
  border-top: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-footer-bg);
  flex-shrink: 0;
}

/* 默认单行胶囊边框 */
.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 10px;
  background: var(--ao-composer-bg);
  border: 1px solid var(--ao-composer-border);
  border-radius: 24px;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--ao-shadow-sm, 0 2px 8px rgba(0, 0, 0, 0.04));
}

/* 文字多行时触发：平滑扩展为大卡片边框 */
.composer.is-expanded {
  flex-direction: column;
  align-items: stretch;
  padding: 12px 14px 10px;
}

.composer:focus-within {
  background: var(--ao-panel-bg);
  border-color: rgba(79, 70, 229, 0.4);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1), 0 4px 16px rgba(0, 0, 0, 0.06);
}

.composer-top-row {
  width: 100%;
}

.chat-textarea {
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-size: 14px;
  line-height: 1.5;
  font-family: inherit;
  color: var(--ao-text-primary);
  box-sizing: border-box;
}
.chat-textarea::placeholder {
  color: var(--ao-text-muted);
}

.chat-textarea--single {
  flex: 1;
  padding: 8px 0;
  max-height: 44px;
  overflow-y: hidden;
}

.chat-textarea--multi {
  width: 100%;
  padding: 2px 4px;
  min-height: 40px;
  max-height: 220px;
  overflow-y: auto;
}

.composer-toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  width: 100%;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.composer-right-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
  flex-shrink: 0;
}

.composer-btn--attach {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none !important;
  background: transparent !important;
  color: var(--ao-text-muted, #94a3b8);
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s ease;
  flex-shrink: 0;
  font-size: 18px;
  margin-bottom: 3px;
}
.is-expanded .composer-btn--attach {
  margin-bottom: 0;
}
.composer-btn--attach:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.12) !important;
  color: var(--theme-primary, #6366f1) !important;
  transform: scale(1.1);
}
.composer-btn--attach:active:not(:disabled) {
  transform: scale(0.95);
}
.composer-btn--attach:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attached-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--ao-panel-border);
  border-radius: 12px;
  padding: 6px 12px;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--ao-text-primary);
  max-width: 100%;
}
.attached-file-chip .file-icon {
  font-size: 16px;
  color: var(--theme-primary);
}
.attached-file-chip .file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.attached-file-chip .remove-btn {
  padding: 0;
  margin-left: 4px;
  font-size: 14px;
  color: var(--ao-text-muted) !important;
}
.attached-file-chip .remove-btn:hover {
  color: var(--el-color-danger) !important;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border: none;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.22s ease;
}
.action-btn--send {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  padding: 0;
  background: var(--ao-chat-send-gradient, linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
  font-size: 15px;
}
.action-btn--send:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
}
.action-btn--send:active {
  transform: scale(0.94);
}

.scale-send-enter-active,
.scale-send-leave-active {
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.scale-send-enter-from,
.scale-send-leave-to {
  opacity: 0;
  transform: scale(0.5);
  width: 0;
  margin: 0;
}

.action-btn--stop {
  position: relative;
  height: 32px;
  padding: 0 14px;
  background: rgba(239, 68, 68, 0.1) !important;
  color: #ef4444 !important;
  border: 1px solid rgba(239, 68, 68, 0.28) !important;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}

.action-btn--stop::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  opacity: 0;
  transition: opacity 0.25s ease;
  z-index: 0;
}

.action-btn--stop > * {
  position: relative;
  z-index: 1;
  transition: all 0.25s ease;
}

.action-btn--stop:hover {
  color: #ffffff !important;
  border-color: #ef4444 !important;
  box-shadow: 0 4px 18px rgba(239, 68, 68, 0.42), 0 0 0 4px rgba(239, 68, 68, 0.15) !important;
  transform: translateY(-2px) scale(1.04);
}

.action-btn--stop:hover::before {
  opacity: 1;
}

.action-btn--stop:hover .stop-icon {
  transform: scale(1.2) rotate(-90deg);
}

.action-btn--stop:active {
  transform: translateY(0) scale(0.96);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3) !important;
}

.chip-image-thumb {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--ao-panel-border);
}

.input-hint {
  margin: 4px 0 0;
  text-align: center;
  font-size: 11px;
  color: var(--ao-text-muted);
}
</style>
