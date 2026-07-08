<script setup lang="ts">
import ChatHeaderBar from '@/components/chat/ChatHeaderBar.vue'
import ChatMessagePanel from '@/components/chat/ChatMessagePanel.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
</script>

<template>
  <section class="chat-main">
    <ChatHeaderBar />
    <ChatMessagePanel />
    <ChatComposer />
  </section>
</template>

<style scoped>
.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-bg);
  box-shadow: 0 16px 40px var(--ao-panel-shadow);
  overflow: hidden;
  position: relative;
  margin-left: 12px;
  transition: margin-left 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 860px) {
  .chat-main {
    margin-left: 0;
    margin-top: 10px;
    min-height: 560px;
  }
}
</style>
