<script setup lang="ts">
import { ref } from 'vue'
import { Close, Document, DocumentAdd, Loading, Promotion, VideoPause } from '@element-plus/icons-vue'
import { useChatView } from '@/composables/useChatView'

const {
  chatStore,
  inputText,
  handleSend,
  handleKeydown,
  handleStop,
  attachedFile,
  uploadingFile,
  handleUploadChatFile,
  clearAttachment
} = useChatView()

const fileInputRef = ref<HTMLInputElement | null>(null)

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
</script>

<template>
  <footer class="chat-input-area">
    <!-- Attached file preview chip -->
    <div v-if="attachedFile" class="attached-file-chip">
      <el-icon class="file-icon"><Document /></el-icon>
      <span class="file-name">{{ attachedFile.name }}</span>
      <el-button class="remove-btn" type="text" :icon="Close" circle @click="clearAttachment" />
    </div>

    <div class="composer" :class="{ disabled: chatStore.streaming }">
      <!-- Attachment upload button -->
      <button
        type="button"
        class="composer-btn composer-btn--attach"
        :disabled="chatStore.streaming || uploadingFile"
        @click="triggerFileSelect"
      >
        <el-icon v-if="uploadingFile" class="is-loading"><Loading /></el-icon>
        <el-icon v-else><DocumentAdd /></el-icon>
      </button>
      <input
        ref="fileInputRef"
        type="file"
        style="display: none"
        accept=".pdf,.docx,.doc,.txt,.md"
        @change="onFileChange"
      />

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
      <button
        v-else
        type="button"
        class="action-btn action-btn--send"
        :disabled="!inputText.trim() && !attachedFile"
        @click="handleSend"
      >
        <el-icon><Promotion /></el-icon>发送
      </button>
    </div>
    <p class="input-hint">AgentOne 可能会犯错，请核实重要信息。</p>
  </footer>
</template>

<style scoped>
.chat-input-area {
  padding: 12px 16px 16px;
  border-top: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-footer-bg);
  flex-shrink: 0;
}
.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 10px 8px 10px;
  background: var(--ao-composer-bg);
  border: 1px solid var(--ao-composer-border);
  border-radius: 24px;
  transition: all 0.22s ease;
}
.composer:focus-within {
  background: var(--ao-panel-bg);
  border-color: rgba(79, 70, 229, 0.4);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}
.composer.disabled {
  opacity: 0.85;
}

.composer-btn--attach {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--ao-text-muted);
  cursor: pointer;
  border-radius: 50%;
  margin-bottom: 2px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.composer-btn--attach:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: var(--theme-primary);
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

.chat-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-size: 14px;
  line-height: 1.5;
  padding: 8px 0;
  max-height: 120px;
  font-family: inherit;
  color: var(--ao-text-primary);
}
.chat-textarea::placeholder {
  color: var(--ao-text-muted);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
  margin-bottom: 2px;
}
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

.input-hint {
  margin: 8px 0 0;
  text-align: center;
  font-size: 11px;
  color: var(--ao-text-muted);
}
</style>
