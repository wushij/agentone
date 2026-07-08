<script setup lang="ts">
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatEmptyState from '@/components/chat/ChatEmptyState.vue'
import { useChatView } from '@/composables/useChatView'

const { chatStore, userStore, messagesRef, handleRegenerate, handleDeleteMessage } = useChatView()
</script>

<template>
  <div ref="messagesRef" class="chat-messages">
    <div v-if="chatStore.loadingMessages" class="messages-loading">
      <el-skeleton :rows="6" animated />
    </div>

    <ChatEmptyState v-else-if="!chatStore.messages.length" />

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
</template>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 12px;
  background: var(--ao-messages-bg);
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.5) transparent;
}
.chat-messages::-webkit-scrollbar {
  width: 6px;
}
.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.45);
  border-radius: 999px;
}

.messages-loading {
  max-width: 600px;
  margin: 0 auto;
}
</style>
