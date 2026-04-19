<template>
  <div class="w-[240px] bg-ctp-mantle text-ctp-text flex flex-col border-l border-ctp-overlay">
    <!-- 标题 -->
    <div class="px-4 py-4 font-bold border-b border-ctp-overlay">
      技能面板
    </div>

    <!-- 技能列表 -->
    <div class="flex-1 overflow-y-auto p-3">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="text-center text-ctp-subtext py-4">
        加载中...
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="text-center text-ctp-pink py-4">
        {{ error }}
      </div>

      <!-- 技能列表 -->
      <div v-else>
        <div
          v-for="skill in skills"
          :key="skill.name"
          class="px-3 py-2 rounded-lg mb-2 cursor-pointer transition-colors"
          :class="[
            selectedSkill === skill.name
              ? 'bg-ctp-surface ring-2 ring-ctp-blue'
              : 'bg-ctp-surface/50 hover:bg-ctp-surface'
          ]"
          @click="selectSkill(skill.name)"
        >
          <div class="font-medium" :style="getSkillColor(skill.category)">
            {{ getSkillIcon(skill.category) }} {{ skill.name }}
          </div>
          <div class="text-xs text-ctp-subtext mt-1 truncate">
            {{ skill.description }}
          </div>
        </div>
      </div>
    </div>

    <!-- 会话统计 -->
    <div class="px-3 py-3 border-t border-ctp-overlay">
      <div class="text-xs text-ctp-subtext mb-2">当前会话统计</div>
      <div class="flex justify-between text-sm">
        <span>消息数</span>
        <span class="text-ctp-blue">{{ messageCount }}</span>
      </div>
      <div class="flex justify-between text-sm mt-1">
        <span>状态</span>
        <span :class="isStreaming ? 'text-ctp-orange' : 'text-ctp-green'">
          {{ isStreaming ? '响应中' : '空闲' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSkillStore } from '../stores/skill'
import { useChatStore } from '../stores/chat'

const skillStore = useSkillStore()
const chatStore = useChatStore()

const skills = computed(() => skillStore.skills)
const selectedSkill = computed(() => skillStore.selectedSkill)
const isLoading = computed(() => skillStore.isLoading)
const error = computed(() => skillStore.error)
const messageCount = computed(() => chatStore.messageCount)
const isStreaming = computed(() => chatStore.isStreaming)

function selectSkill(name: string | null) {
  skillStore.selectSkill(name)
}

function getSkillIcon(category: string): string {
  const icons: Record<string, string> = {
    coding: '🔧',
    lifestyle: '🏠',
    learning: '📚',
    ecommerce: '🛒',
    system: '⚙️',
  }
  return icons[category] || '⚡'
}

function getSkillColor(category: string): string {
  const colors: Record<string, string> = {
    coding: 'color: #fab387',
    lifestyle: 'color: #a6e3a1',
    learning: 'color: #f38ba8',
    ecommerce: 'color: #89b4fa',
    system: 'color: #94e2d5',
  }
  return colors[category] || 'color: #cdd6f4'
}

onMounted(() => {
  skillStore.loadSkills()
})
</script>