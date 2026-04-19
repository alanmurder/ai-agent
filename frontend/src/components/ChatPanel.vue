<template>
  <div class="flex-1 flex flex-col bg-ctp-base">
    <!-- 顶部标题栏 -->
    <div class="px-4 py-3 bg-ctp-surface border-b border-ctp-overlay">
      <div class="text-ctp-text font-medium">
        {{ currentSession?.title || '新会话' }}
      </div>
      <div class="text-xs text-ctp-subtext">
        消息数: {{ messageCount }}
      </div>
    </div>

    <!-- 消息列表 -->
    <div
      ref="scrollRef"
      class="flex-1 overflow-y-auto p-4"
    >
      <!-- 空状态 -->
      <div
        v-if="messages.length === 0"
        class="flex flex-col items-center justify-center h-full text-ctp-subtext"
      >
        <div class="text-4xl mb-4">💬</div>
        <div class="text-lg">开始新对话</div>
        <div class="text-sm mt-2">输入消息与 AI Agent 交流</div>
      </div>

      <!-- 消息列表 -->
      <MessageItem
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />
    </div>

    <!-- 输入框 -->
    <InputBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { useSessionStore } from '../stores/session'
import MessageItem from './MessageItem.vue'
import InputBar from './InputBar.vue'

const chatStore = useChatStore()
const sessionStore = useSessionStore()

const scrollRef = ref<HTMLDivElement | null>(null)

const messages = computed(() => chatStore.messages)
const messageCount = computed(() => chatStore.messageCount)
const currentSession = computed(() => sessionStore.currentSession)

// 自动滚动到底部
watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      if (scrollRef.value) {
        scrollRef.value.scrollTop = scrollRef.value.scrollHeight
      }
    })
  }
)

// 监听流式内容更新，平滑滚动
watch(
  () => chatStore.currentContent,
  () => {
    if (chatStore.isStreaming && scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  }
)
</script>