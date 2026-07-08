<script setup lang="ts">
import { computed } from 'vue'
import type { KnowledgeSegment } from '@/api/admin'

const props = defineProps<{
  segment: KnowledgeSegment
}>()

const qaPair = computed(() => parseQaSegment(props.segment.text))

function parseQaSegment(text: string): { question: string; answer: string } | null {
  const normalized = text.replace(/\r\n/g, '\n').trim()
  const qMatch = normalized.match(/^问[:：]\s*([\s\S]*?)(?:\n答[:：]|$)/)
  const aMatch = normalized.match(/答[:：]\s*([\s\S]*)$/)
  if (!qMatch && !aMatch) return null
  return {
    question: (qMatch?.[1] || '').trim(),
    answer: (aMatch?.[1] || '').trim()
  }
}
</script>

<template>
  <article class="kb-segment-card">
    <header class="kb-segment-card__head">
      <span class="kb-segment-card__index">#{{ segment.index }}</span>
      <span class="kb-segment-card__file">{{ segment.fileName }}</span>
      <span class="kb-segment-card__meta">{{ segment.charCount }} 字</span>
    </header>

    <div v-if="qaPair" class="kb-segment-card__qa">
      <div class="kb-segment-card__q">
        <span class="kb-segment-card__label">问</span>
        <p>{{ qaPair.question }}</p>
      </div>
      <div class="kb-segment-card__a">
        <span class="kb-segment-card__label">答</span>
        <p>{{ qaPair.answer }}</p>
      </div>
    </div>
    <pre v-else class="kb-segment-card__text">{{ segment.text }}</pre>
  </article>
</template>

<style scoped>
.kb-segment-card {
  border: 1px solid var(--ao-panel-border);
  border-radius: 14px;
  background: var(--ao-panel-bg);
  padding: 14px 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.kb-segment-card:hover {
  border-color: color-mix(in srgb, var(--theme-primary) 28%, transparent);
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.06);
}

.kb-segment-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.kb-segment-card__index {
  font-size: 11px;
  font-weight: 800;
  color: var(--theme-primary);
  background: var(--theme-primary-muted);
  padding: 2px 8px;
  border-radius: 999px;
}

.kb-segment-card__file {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kb-segment-card__meta {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.kb-segment-card__text {
  margin: 0;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  color: var(--ao-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.kb-segment-card__qa {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kb-segment-card__q,
.kb-segment-card__a {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.kb-segment-card__label {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.kb-segment-card__q .kb-segment-card__label {
  background: rgba(79, 70, 229, 0.1);
  color: var(--theme-primary);
}

.kb-segment-card__a .kb-segment-card__label {
  background: rgba(13, 148, 136, 0.1);
  color: #0d9488;
}

.kb-segment-card__q p,
.kb-segment-card__a p {
  margin: 0;
  flex: 1;
  font-size: 13px;
  line-height: 1.7;
  color: var(--ao-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
