import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message } from '../types'
import { wsClient } from '../api/websocket'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const currentContent = ref('')
  const currentSessionId = ref<string | null>(null)

  // Getters
  const messageCount = computed(() => messages.value.length)

  // 生成唯一 ID
  const generateId = () => `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

  // Actions
  function sendMessage(content: string, userId: string = 'default') {
    // 添加用户消息
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    messages.value.push(userMessage)

    // 创建 AI 消息占位
    const aiMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    messages.value.push(aiMessage)

    // 重置流式状态
    isStreaming.value = true
    currentContent.value = ''

    // 发送到 WebSocket
    wsClient.send({
      message: content,
      user_id: userId,
      session_id: currentSessionId.value,
    })
  }

  function appendChunk(chunk: string) {
    currentContent.value += chunk

    // 更新最后一条 AI 消息的内容
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
      lastMessage.content = currentContent.value
    }
  }

  function completeMessage(sessionId: string) {
    isStreaming.value = false
    currentSessionId.value = sessionId

    // 标记最后一条消息完成
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage && lastMessage.role === 'assistant') {
      lastMessage.isStreaming = false
    }
  }

  function clearMessages() {
    messages.value = []
    currentContent.value = ''
    currentSessionId.value = null
  }

  // 初始化 WebSocket 处理器
  function initWebSocket() {
    wsClient.onMessage((data) => {
      if (data.type === 'chunk') {
        appendChunk(data.content)
      } else if (data.type === 'complete') {
        completeMessage(data.session_id)
      }
    })
  }

  return {
    messages,
    isStreaming,
    currentContent,
    currentSessionId,
    messageCount,
    sendMessage,
    appendChunk,
    completeMessage,
    clearMessages,
    initWebSocket,
  }
})