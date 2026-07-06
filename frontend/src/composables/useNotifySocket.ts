import { ElNotification } from 'element-plus'
import { useNotifyStore } from '@/stores/notify'
import { useAgentStore } from '@/stores/agent'
import type { NotificationItem } from '@/types'

type WsMessageType =
  | 'ping'
  | 'pong'
  | 'notification'
  | 'agent_status'
  | 'task_progress'
  | 'system'
  | 'subscribe'
  | 'unsubscribe'
  | 'kick'
  | 'error'
  | 'ack'

interface WsEnvelope {
  type: WsMessageType
  id?: string
  timestamp?: string
  payload?: Record<string, unknown>
}

let socket: WebSocket | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempt = 0
let currentToken = ''
let connectImpl: ((token: string) => void) | null = null
const subscribedTopics = new Set<string>()

const MAX_RECONNECT_DELAY = 30000

function getWsUrl(token: string): string {
  const envUrl = import.meta.env.VITE_WS_BASE_URL
  if (envUrl) {
    const sep = envUrl.includes('?') ? '&' : '?'
    return `${envUrl}${sep}token=${encodeURIComponent(token)}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws/notify?token=${encodeURIComponent(token)}`
}

function clearTimers() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function scheduleReconnect() {
  const notifyStore = useNotifyStore()
  notifyStore.setWsConnected(false)
  notifyStore.setReconnecting(true)

  const delay = Math.min(1000 * 2 ** reconnectAttempt, MAX_RECONNECT_DELAY)
  reconnectAttempt += 1

  reconnectTimer = setTimeout(() => {
    if (currentToken && connectImpl) connectImpl(currentToken)
  }, delay)
}

function startHeartbeat(ws: WebSocket) {
  heartbeatTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000)
}

function flushSubscriptions() {
  if (!socket || socket.readyState !== WebSocket.OPEN || !subscribedTopics.size) return
  socket.send(JSON.stringify({ type: 'subscribe', payload: { topics: [...subscribedTopics] } }))
}

function showNotification(payload: Record<string, unknown>) {
  const notifyStore = useNotifyStore()
  const item: Omit<NotificationItem, 'read'> = {
    id: String(payload.id ?? `notif_${Date.now()}`),
    level: (payload.level as NotificationItem['level']) ?? 'info',
    title: String(payload.title ?? '系统通知'),
    body: String(payload.body ?? ''),
    timestamp: String(payload.timestamp ?? new Date().toISOString()),
    action: payload.action as NotificationItem['action']
  }

  notifyStore.addNotification(item)

  const action = item.action
  ElNotification({
    title: item.title,
    message: item.body,
    type:
      item.level === 'error'
        ? 'error'
        : item.level === 'warning'
          ? 'warning'
          : item.level === 'success'
            ? 'success'
            : 'info',
    duration: 5000,
    onClick: () => {
      notifyStore.markRead(item.id)
      if (action?.route) {
        import('@/router').then(({ default: router }) => {
          void router.push(action.route!)
        })
      }
    }
  })
}

function handleMessage(raw: string) {
  let msg: WsEnvelope
  try {
    msg = JSON.parse(raw) as WsEnvelope
  } catch {
    return
  }

  switch (msg.type) {
    case 'pong':
      break
    case 'notification':
    case 'system':
      if (msg.payload) showNotification(msg.payload)
      break
    case 'kick':
      currentToken = ''
      import('@/stores/user').then(({ useUserStore }) => {
        void useUserStore().logout()
        import('@/utils/session').then(({ handleUnauthorized }) => void handleUnauthorized())
      })
      break
    case 'error':
      if (msg.payload?.code === 'WS_SUBSCRIBE_DENIED') {
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.warning('部分主题订阅被拒绝')
        })
      }
      break
    case 'agent_status':
      if (msg.payload) useAgentStore().applyStatus(msg.payload)
      break
    default:
      break
  }
}

export function useNotifySocket() {
  function connect(token: string) {
    if (!token) return
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      if (currentToken === token) return
      disconnect()
    }

    currentToken = token
    connectImpl = connect
    clearTimers()

    const notifyStore = useNotifyStore()
    notifyStore.setReconnecting(true)

    try {
      socket = new WebSocket(getWsUrl(token))
    } catch {
      scheduleReconnect()
      return
    }

    socket.onopen = () => {
      reconnectAttempt = 0
      notifyStore.setWsConnected(true)
      notifyStore.setReconnecting(false)
      startHeartbeat(socket!)
      flushSubscriptions()
    }

    socket.onmessage = (event) => {
      handleMessage(String(event.data))
    }

    socket.onclose = () => {
      clearTimers()
      if (currentToken) scheduleReconnect()
    }

    socket.onerror = () => {
      socket?.close()
    }
  }

  function disconnect() {
    currentToken = ''
    connectImpl = null
    clearTimers()
    subscribedTopics.clear()
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    const notifyStore = useNotifyStore()
    notifyStore.setWsConnected(false)
    notifyStore.setReconnecting(false)
  }

  function subscribe(topics: string[]) {
    topics.forEach((topic) => subscribedTopics.add(topic))
    flushSubscriptions()
  }

  function unsubscribe(topics: string[]) {
    topics.forEach((topic) => subscribedTopics.delete(topic))
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'unsubscribe', payload: { topics } }))
    }
  }

  return { connect, disconnect, subscribe, unsubscribe }
}
