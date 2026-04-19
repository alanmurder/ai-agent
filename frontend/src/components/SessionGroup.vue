<template>
  <div class="mb-4">
    <div class="text-xs text-ctp-subtext mb-2 px-1">
      {{ title }}
    </div>
    <div
      v-for="session in sessions"
      :key="session.id"
      class="px-3 py-2 rounded-lg mb-1 cursor-pointer text-sm truncate transition-colors"
      :class="[
        session.id === currentId
          ? 'bg-ctp-surface text-ctp-text'
          : 'text-ctp-subtext hover:bg-ctp-surface/50'
      ]"
      @click="$emit('select', session.id)"
    >
      {{ session.title }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '../types'

defineProps<{
  title: string
  sessions: Session[]
  currentId: string | null
}>()

defineEmits<{
  (e: 'select', id: string): void
}>()
</script>