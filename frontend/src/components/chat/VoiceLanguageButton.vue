<script setup lang="ts">
import { ref } from 'vue'
import { Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  currentText?: string
}>()

const emit = defineEmits<{
  (e: 'updateText', text: string): void
}>()

const isListening = ref(false)
let recognition: any = null
let baseInputText = ''

function toggleVoice() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    ElMessage.info('当前浏览器未提供 Web Speech API，请使用 Chrome 或 Edge 体验语音听写')
    return
  }

  if (isListening.value) {
    try {
      recognition?.stop()
    } catch {
      /* ignore */
    }
    isListening.value = false
    ElMessage.info('已手动结束录音')
    return
  }

  try {
    recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'zh-CN'
    baseInputText = (props.currentText || '').trim()

    recognition.onstart = () => {
      isListening.value = true
      ElMessage.success('已开启录音听写，再次点击麦克风图标结束录音')
    }

    recognition.onresult = (event: any) => {
      let fullSpeech = ''

      for (let i = 0; i < event.results.length; i++) {
        fullSpeech += event.results[i][0].transcript
      }

      const cleanSpeech = fullSpeech.trim()
      if (cleanSpeech) {
        const combined = baseInputText ? `${baseInputText} ${cleanSpeech}` : cleanSpeech
        emit('updateText', combined)
      }
    }

    recognition.onerror = (e: any) => {
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        isListening.value = false
        ElMessage.warning(`语音解析提示: ${e.error || '请重试'}`)
      }
    }

    recognition.onend = () => {
      if (isListening.value) {
        try {
          recognition?.start()
        } catch {
          isListening.value = false
        }
      }
    }

    recognition.start()
  } catch {
    isListening.value = false
    ElMessage.error('无法启动麦克风录音，请检查设备权限')
  }
}
</script>

<template>
  <button
    type="button"
    class="voice-btn"
    :class="{ 'is-listening': isListening }"
    :title="isListening ? '点击结束录音' : '点击开始语音听写'"
    @click="toggleVoice"
  >
    <el-icon class="voice-icon"><Microphone /></el-icon>
  </button>
</template>

<style scoped>
.voice-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--ao-text-secondary, #64748b);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.voice-btn:hover {
  background: var(--ao-panel-border, rgba(0, 0, 0, 0.06));
  color: var(--ao-text-primary, #1e293b);
}
.voice-btn.is-listening {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
  animation: pulse-voice 1.2s infinite ease-in-out;
}
@keyframes pulse-voice {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}
.voice-icon {
  font-size: 16px;
}
</style>
