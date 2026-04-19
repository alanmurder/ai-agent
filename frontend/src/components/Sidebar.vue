<template>
  <div class="w-[220px] bg-ctp-mantle text-ctp-text flex flex-col">
    <!-- 标题 -->
    <div class="px-4 py-4 font-bold text-lg border-b border-ctp-overlay">
      AI Agent
    </div>

    <!-- 新建会话按钮 -->
    <div class="px-3 py-3">
      <button
        class="w-full px-4 py-2 bg-ctp-surface rounded-lg text-sm hover:bg-ctp-overlay transition-colors flex items-center gap-2"
        @click="createNewSession"
      >
        <span>+</span>
        <span>新建会话</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto px-3">
      <!-- 今天 -->
      <SessionGroup
        v-if="todaySessions.length > 0"
        title="今天"
        :sessions="todaySessions"
        :current-id="currentId"
        @select="switchSession"
      />

      <!-- 昨天 -->
      <SessionGroup
        v-if="yesterdaySessions.length > 0"
        title="昨天"
        :sessions="yesterdaySessions"
        :current-id="currentId"
        @select="switchSession"
      />

      <!-- 更早 -->
      <SessionGroup
        v-if="olderSessions.length > 0"
        title="更早"
        :sessions="olderSessions"
        :current-id="currentId"
        @select="switchSession"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../stores/session'
import { useChatStore } from '../stores/chat'
import SessionGroup from './SessionGroup.vue'

const sessionStore = useSessionStore()
const chatStore = useChatStore()

const todaySessions = computed(() => sessionStore.todaySessions)
const yesterdaySessions = computed(() => sessionStore.yesterdaySessions)
const olderSessions = computed(() => sessionStore.olderSessions)
const currentId = computed(() => sessionStore.currentId)

function createNewSession() {
  sessionStore.createSession()
  chatStore.clearMessages()
}

function switchSession(id: string) {
  sessionStore.switchSession(id)
  // TODO: 加载历史消息
}
</script>