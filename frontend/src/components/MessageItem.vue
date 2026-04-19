<template>
  <div
    class="flex gap-3 mb-4"
    :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <!-- AI 头像 -->
    <div
      v-if="message.role === 'assistant'"
      class="w-8 h-8 rounded-full flex items-center justify-center text-sm"
      :class="message.isStreaming ? 'animate-pulse' : ''"
      style="background: #89b4fa;"
    >
      AI
    </div>

    <!-- 消息内容 -->
    <div
      class="max-w-[70%] px-4 py-3 rounded-lg"
      :class="[
        message.role === 'user'
          ? 'bg-ctp-blue text-ctp-base'
          : 'bg-ctp-surface text-ctp-text'
      ]"
    >
      <!-- 时间戳 -->
      <div
        class="text-xs mb-1 opacity-70"
        :class="message.role === 'user' ? 'text-ctp-base' : 'text-ctp-subtext'"
      >
        {{ formatTime(message.timestamp) }}
        <span v-if="message.role === 'assistant'"> · AI Agent</span>
      </div>

      <!-- 消息文本 -->
      <div
        v-if="message.role === 'user'"
        class="whitespace-pre-wrap"
      >
        {{ message.content }}
      </div>

      <!-- AI 消息使用 Markdown 渲染 -->
      <div
        v-else
        class="message-content"
        v-html="renderedContent"
      ></div>

      <!-- 流式加载指示器 -->
      <div
        v-if="message.isStreaming && !message.content"
        class="flex gap-1"
      >
        <span class="w-2 h-2 bg-ctp-blue rounded-full animate-bounce"></span>
        <span class="w-2 h-2 bg-ctp-blue rounded-full animate-bounce" style="animation-delay: 0.1s;"></span>
        <span class="w-2 h-2 bg-ctp-blue rounded-full animate-bounce" style="animation-delay: 0.2s;"></span>
      </div>
    </div>

    <!-- 用户头像 -->
    <div
      v-if="message.role === 'user'"
      class="w-8 h-8 rounded-full flex items-center justify-center text-sm"
      style="background: #a6e3a1;"
    >
      你
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '../types'

const props = defineProps<{
  message: Message
}>()

// 格式化时间
function formatTime(date: Date): string {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 渲染 Markdown 内容
const renderedContent = computed(() => {
  if (!props.message.content) return ''

  // 配置 marked 选项
  marked.setOptions({
    breaks: true,
    gfm: true,
  })

  return marked.parse(props.message.content) as string
})
</script>