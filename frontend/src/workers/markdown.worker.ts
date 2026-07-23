/**
 * src/workers/markdown.worker.ts — Markdown 与大文本增量解析 Worker
 */

self.onmessage = (event: MessageEvent<{ text: string }>) => {
  const { text } = event.data
  if (!text) {
    self.postMessage({ result: '' })
    return
  }
  // 在 Web Worker 后台执行大文本清洗与标记提取
  const processed = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
  self.postMessage({ result: processed })
}
