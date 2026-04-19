import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Skill } from '../types'

export const useSkillStore = defineStore('skill', () => {
  // State
  const skills = ref<Skill[]>([])
  const selectedSkill = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function loadSkills() {
    isLoading.value = true
    error.value = null

    try {
      const response = await fetch('/api/skills')
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }
      const data = await response.json()
      skills.value = data.skills || []
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载技能失败'
      console.error('Failed to load skills:', e)
    } finally {
      isLoading.value = false
    }
  }

  function selectSkill(name: string | null) {
    selectedSkill.value = name
  }

  function getSkillByName(name: string): Skill | undefined {
    return skills.value.find(s => s.name === name)
  }

  return {
    skills,
    selectedSkill,
    isLoading,
    error,
    loadSkills,
    selectSkill,
    getSkillByName,
  }
})