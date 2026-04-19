<template>
  <div class="px-4 py-3 bg-ctp-surface border-t border-ctp-overlay">
    <div class="flex gap-3 items-end">
      <!-- 输入框 -->
      <textarea
        ref="inputRef"
        v-model="inputText"
        class="flex-1 bg-ctp-mantle text-ctp-text rounded-lg px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-ctp-blue placeholder-ctp-subtext"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        rows="1"
        :disabled="isStreaming"
        @keydown="handleKeydown"
        @input="adjustHeight"
      ></textarea>

      <!-- 发送按钮 -->
      <button
        class="px-4 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
        :class="[
          isStreaming || !inputText.trim()
            ? 'bg-ctp-overlay text-ctp-subtext cursor-not-allowed'
            : 'bg-ctp-blue text-ctp-base hover:bg-ctp-blue/80'
        ]"
        :disabled="isStreaming || !inputText.trim()"
        @click="sendMessage"
      >
        <span v-if="isStreaming">等待...</span>
        <span v-else>发送</span>
      </button>
    </div>

    <!-- 状态提示 -->
    <div v-if="isStreaming" class="mt-2 text-xs text-ctp-subtext flex items-center gap-2">
      <span class="w-1.5 h-1.5 bg-ctp-green rounded-full animate-pulse"></span>
      AI 正在回复...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()

const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)

// 发送状态
const isStreaming = computed(() => chatStore.isStreaming)

// 发送消息
function sendMessage() {
  const content = inputText.value.trim()
  if (!content || chatStore.isStreaming) return

  chatStore.sendMessage(content)
  inputText.value = ''

  // 重置输入框高度
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
    }
  })
}

// 处理键盘事件
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 自动调整输入框高度
function adjustHeight() {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 150) + 'px'
  }
}

// 自动聚焦
onMounted(() => {
  inputRef.value?.focus()
})
</script>