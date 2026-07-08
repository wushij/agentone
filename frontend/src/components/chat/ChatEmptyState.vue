<script setup lang="ts">
import { useChatView } from '@/composables/useChatView'

const { inputText, handleSend } = useChatView()

async function sendPrompt(text: string) {
  inputText.value = text
  await handleSend()
}
</script>

<template>
  <div class="fresh-state">
    <div class="empty-illustration">
      <div class="empty-orbit empty-orbit--a" />
      <div class="empty-orbit empty-orbit--b" />
      <div class="empty-core">
        <svg viewBox="0 0 64 64" width="44" height="44" fill="none">
          <circle cx="32" cy="32" r="28" stroke="url(#empty-grad)" stroke-width="2" opacity="0.4" />
          <path
            d="M22 38c0-5.5 4.5-12 10-12s10 6.5 10 12"
            stroke="#4f46e5"
            stroke-width="2.5"
            stroke-linecap="round"
          />
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
      <button type="button" class="fresh-state__chip" @click="sendPrompt('AgentOne 是什么系统？技术架构是什么？')">
        AgentOne 是什么系统？技术架构是什么？
      </button>
      <button type="button" class="fresh-state__chip" @click="sendPrompt('AI 对话的完整流程是怎样的？')">
        AI 对话的完整流程是怎样的？
      </button>
      <button type="button" class="fresh-state__chip" @click="sendPrompt('内置工具有哪些？各自能做什么？')">
        内置工具有哪些？各自能做什么？
      </button>
    </div>
  </div>
</template>

<style scoped>
.fresh-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 24px;
}

.empty-illustration {
  position: relative;
  width: 140px;
  height: 140px;
  margin-bottom: 24px;
}
.empty-orbit {
  position: absolute;
  border-radius: 50%;
  border: 1.5px dashed rgba(99, 102, 241, 0.25);
}
.empty-orbit--a {
  inset: 0;
  animation: orbit-spin 20s linear infinite;
}
.empty-orbit--b {
  inset: 16px;
  animation: orbit-spin 14s linear infinite reverse;
}
.empty-core {
  position: absolute;
  inset: 32px;
  border-radius: 50%;
  background: var(--ao-panel-btn-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12px 40px rgba(79, 70, 229, 0.12);
}
@keyframes orbit-spin {
  to {
    transform: rotate(360deg);
  }
}

.fresh-state h3 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: var(--ao-text-primary);
  line-height: 1.25;
}
.fresh-state__chips {
  margin-top: 28px;
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 12px;
  max-width: 100%;
  overflow-x: auto;
  padding: 4px 12px;
  scrollbar-width: none; /* Firefox */
}
.fresh-state__chips::-webkit-scrollbar {
  display: none; /* Safari and Chrome */
}
.fresh-state__chip {
  border: 1px solid var(--ao-chip-border);
  background: var(--ao-panel-bg);
  color: var(--ao-text-secondary);
  border-radius: 999px;
  padding: 10px 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.fresh-state__chip:hover {
  border-color: rgba(99, 102, 241, 0.3);
  color: var(--theme-primary);
  background: var(--theme-primary-muted);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
}
</style>
