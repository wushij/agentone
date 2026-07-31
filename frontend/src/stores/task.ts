import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface TaskProgress {
  taskId: string
  progress: number
  detail: string
  status: string
}

export const useTaskStore = defineStore('task', () => {
  // taskId -> 最新进度（WS 实时推送写入，任务中心页读取）
  const progressMap = ref<Record<string, TaskProgress>>({})

  function applyProgress(payload: Record<string, unknown>) {
    const taskId = String(payload.taskId ?? '')
    if (!taskId) return
    progressMap.value[taskId] = {
      taskId,
      progress: Number(payload.progress ?? 0),
      detail: String(payload.detail ?? ''),
      status: String(payload.status ?? 'running')
    }
  }

  function getProgress(taskId: string): TaskProgress | undefined {
    return progressMap.value[taskId]
  }

  function reset() {
    progressMap.value = {}
  }

  return { progressMap, applyProgress, getProgress, reset }
})
