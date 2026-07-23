<script setup lang="ts">
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMainPanel from '@/components/chat/ChatMainPanel.vue'
import { useChatViewProvider } from '@/composables/useChatView'

const { historyCollapsed } = useChatViewProvider()
</script>

<template>
  <div class="chat-view ao-page" :class="{ 'chat-view--collapsed': historyCollapsed }">
    <ChatSidebar />
    <ChatMainPanel />
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

.chat-view--collapsed :deep(.chat-main) {
  margin-left: 10px;
}

@media (max-width: 860px) {
  .chat-view {
    flex-direction: column;
    height: auto;
    min-height: auto;
  }
}
</style>
