<template>
  <div class="h-screen flex bg-ctp-base text-ctp-text overflow-hidden">
    <!-- 左侧：会话列表 -->
    <Sidebar />

    <!-- 中间：聊天区域 -->
    <ChatPanel />

    <!-- 右侧：技能面板 -->
    <SkillPanel />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatPanel from './components/ChatPanel.vue'
import SkillPanel from './components/SkillPanel.vue'
import { useChatStore } from './stores/chat'
import { useSessionStore } from './stores/session'
import { wsClient } from './api/websocket'

const chatStore = useChatStore()
const sessionStore = useSessionStore()

onMounted(async () => {
  // 初始化会话
  sessionStore.init()

  // 初始化 WebSocket 处理器
  chatStore.initWebSocket()

  // 连接 WebSocket
  try {
    await wsClient.connect()
    console.log('WebSocket connected')
  } catch (e) {
    console.error('WebSocket connection failed:', e)
  }
})
</script>