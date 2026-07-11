import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { VolumeDetail, PlotEventDetail, ChapterPlan, ChapterOutline, SceneSkeleton } from '../types/v2'
import {
  generateVolume, saveVolume, generatePlotNodes, savePlotNode,
  planChapters, saveChapterPlan, generateChapterOutline, saveChapterOutline,
  designScenes, saveScene,
} from '../api/v2'

export const usePlanningStore = defineStore('planning', () => {
  const projectId = ref('')
  const volumes = ref<VolumeDetail[]>([])
  const plotNodes = ref<PlotEventDetail[]>([])
  const chapterPlans = ref<ChapterPlan[]>([])
  const chapterOutlines = ref<ChapterOutline[]>([])
  const scenes = ref<SceneSkeleton[]>([])
  const loading = ref(false)
  const error = ref('')

  async function generateVolumeDetail(pid: string, volumeNo: number, masterOutline: any) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      const r = await generateVolume(pid, volumeNo, masterOutline)
      const existing = volumes.value.filter(v => v.volumeNo !== volumeNo)
      volumes.value = [...existing, r]
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveVolumeDetail(pid: string, volumeNo: number, data: any) {
    return saveVolume(pid, volumeNo, data)
  }

  async function generateNodes(pid: string, chapterPlan: any, masterOutline: any) {
    loading.value = true
    error.value = ''
    try {
      const r = await generatePlotNodes(pid, chapterPlan, masterOutline)
      plotNodes.value = r.events
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveNode(pid: string, eventId: string, data: any) {
    return savePlotNode(pid, eventId, data)
  }

  async function planChaptersForVolume(pid: string, masterOutline: any, events: any[], targetWordcount?: number) {
    loading.value = true
    error.value = ''
    try {
      const r = await planChapters(pid, masterOutline, events, targetWordcount)
      chapterPlans.value = r.chapterAssignments || []
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveChapterPlanData(pid: string, chapterNo: number | string, data: any) {
    return saveChapterPlan(pid, chapterNo, data)
  }

  async function generateOutline(pid: string, chapterNo: number | string, chapterPlan: any) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateChapterOutline(pid, chapterNo, chapterPlan)
      const existing = chapterOutlines.value.filter(c => c.chapterNo !== chapterNo)
      chapterOutlines.value = [...existing, r]
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveOutline(pid: string, chapterNo: number | string, data: any) {
    return saveChapterOutline(pid, chapterNo, data)
  }

  async function designScenesForChapter(pid: string, chapterOutline: any) {
    loading.value = true
    error.value = ''
    try {
      const r = await designScenes(pid, chapterOutline)
      scenes.value = r.scenes
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveSceneData(pid: string, sceneId: string, data: any) {
    return saveScene(pid, sceneId, data)
  }

  async function generatePlanning(pid: string) {
    loading.value = true
    try {
      await generateVolumeDetail(pid, 1, {})
      await generateNodes(pid, {}, {})
      await planChaptersForVolume(pid, {}, [], 30000)
      await generateOutline(pid, 1, {})
      return {
        volumes: volumes.value,
        plotNodes: plotNodes.value,
        chapterPlans: chapterPlans.value,
        chapterOutlines: chapterOutlines.value,
      }
    } finally {
      loading.value = false
    }
  }

  function savePlanning(pid: string, data: any) {
    if (data.volumes) volumes.value = data.volumes
    if (data.plotNodes) plotNodes.value = data.plotNodes
    if (data.chapterPlans) chapterPlans.value = data.chapterPlans
    if (data.chapterOutlines) chapterOutlines.value = data.chapterOutlines
  }

  return {
    projectId, volumes, plotNodes, chapterPlans, chapterOutlines, scenes, loading, error,
    generateVolumeDetail, saveVolumeDetail, generateNodes, saveNode,
    planChaptersForVolume, saveChapterPlanData, generateOutline, saveOutline,
    designScenesForChapter, saveSceneData, generatePlanning, savePlanning,
  }
})
