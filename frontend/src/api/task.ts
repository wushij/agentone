import request from './request'
import type { ApiListParams, ApiPage } from '@/types/pagination'
import { normalizePage } from '@/utils/normalizePage'

export interface TaskItem {
  id: string
  kind: string
  title: string
  input: string
  status: string
  progress: number
  result?: string
  error?: string
  createdAt?: string
  updatedAt?: string
}

export function createTask(input: string, title = '', kind = 'agent') {
  return request.post<{ taskId: string }>('/tasks', { input, title, kind }).then((r) => r.data)
}

export function fetchTasks(params?: ApiListParams) {
  return request.get<ApiPage<TaskItem>>('/tasks', { params }).then((r) => normalizePage<TaskItem>(r.data))
}

export function fetchTask(taskId: string) {
  return request.get<TaskItem>(`/tasks/${taskId}`).then((r) => r.data)
}
