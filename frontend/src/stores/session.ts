import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session } from '../types'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const currentId = ref<string | null>(null)

  // Getters
  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentId.value)
  )

  const todaySessions = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return sessions.value.filter(s => s.createdAt >= today)
  })

  const yesterdaySessions = computed(() => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    yesterday.setHours(0, 0, 0, 0)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return sessions.value.filter(s => s.createdAt >= yesterday && s.createdAt < today)
  })

  const olderSessions = computed(() => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    yesterday.setHours(0, 0, 0, 0)
    return sessions.value.filter(s => s.createdAt < yesterday)
  })

  // 生成唯一 ID
  const generateId = () => `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

  // Actions
  function createSession(title: string = '新会话'): Session {
    const session: Session = {
      id: generateId(),
      title,
      createdAt: new Date(),
      messageCount: 0,
    }
    sessions.value.unshift(session)
    currentId.value = session.id
    return session
  }

  function switchSession(id: string) {
    currentId.value = id
  }

  function updateSessionTitle(id: string, title: string) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      session.title = title
    }
  }

  function updateMessageCount(id: string, count: number) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      session.messageCount = count
    }
  }

  function deleteSession(id: string) {
    const index = sessions.value.findIndex(s => s.id === id)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      if (currentId.value === id) {
        currentId.value = sessions.value[0]?.id || null
      }
    }
  }

  // 初始化，创建一个默认会话
  function init() {
    if (sessions.value.length === 0) {
      createSession()
    }
  }

  return {
    sessions,
    currentId,
    currentSession,
    todaySessions,
    yesterdaySessions,
    olderSessions,
    createSession,
    switchSession,
    updateSessionTitle,
    updateMessageCount,
    deleteSession,
    init,
  }
})