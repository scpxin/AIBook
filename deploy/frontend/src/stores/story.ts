import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StoryMaster, VolumeOutline } from '../types/v2'
import { generateStoryMaster, generateStoryVolumes, checkStoryConsistency } from '../api/v2'

export const useStoryStore = defineStore('story', () => {
  const projectId = ref('')
  const masterStory = ref<StoryMaster | null>(null)
  const volumes = ref<VolumeOutline[]>([])
  const summary = ref('')
  const theme = ref('')
  const loading = ref(false)
  const error = ref('')

  async function generateMaster(pid: string, protagonist: any, world: any, characters: any[]) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      masterStory.value = await generateStoryMaster(pid, protagonist, world, characters)
      theme.value = masterStory.value?.theme || ''
      summary.value = masterStory.value?.theme || ''
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateVolumesList(pid: string, volumeCount?: number) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateStoryVolumes(pid, masterStory.value, volumeCount)
      volumes.value = r.volumes
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function checkConsistency(pid: string, characters: any[]) {
    loading.value = true
    error.value = ''
    try {
      return await checkStoryConsistency(pid, masterStory.value, characters)
    } catch (e: any) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    projectId, masterStory, volumes, summary, theme, loading, error,
    generateMaster, generateVolumesList, checkConsistency,
  }
})
