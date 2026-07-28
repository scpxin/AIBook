import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { VolumeDetail, PlotEventDetail, ChapterPlan, ChapterOutline, SceneSkeleton, MasterOutline } from '../types/v2'
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

  async function generateVolumeDetail(pid: string, volumeNo: number, masterOutline: MasterOutline) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      const r = await generateVolume(pid, volumeNo, masterOutline)
      const existing = volumes.value.filter(v => v.volumeNo !== volumeNo)
      volumes.value = [...existing, r]
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveVolumeDetail(pid: string, volumeNo: number, data: Record<string, unknown>) {
    return saveVolume(pid, volumeNo, data)
  }

  async function generateNodes(pid: string, chapterPlan: ChapterPlan, masterOutline: MasterOutline) {
    loading.value = true
    error.value = ''
    try {
      const r = await generatePlotNodes(pid, chapterPlan, masterOutline)
      plotNodes.value = r.events
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveNode(pid: string, eventId: string, data: Record<string, unknown>) {
    return savePlotNode(pid, eventId, data)
  }

  async function planChaptersForVolume(pid: string, masterOutline: MasterOutline, events: PlotEventDetail[], targetWordcount?: number) {
    loading.value = true
    error.value = ''
    try {
      const r = await planChapters(pid, masterOutline, events, targetWordcount)
      chapterPlans.value = r.chapterAssignments || []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveChapterPlanData(pid: string, chapterNo: number | string, data: Record<string, unknown>) {
    return saveChapterPlan(pid, chapterNo, data)
  }

  async function generateOutline(pid: string, chapterNo: number | string, chapterPlan: ChapterPlan) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateChapterOutline(pid, chapterNo, chapterPlan)
      const existing = chapterOutlines.value.filter(c => c.chapterNo !== chapterNo)
      chapterOutlines.value = [...existing, r]
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveOutline(pid: string, chapterNo: number | string, data: Record<string, unknown>) {
    return saveChapterOutline(pid, chapterNo, data)
  }

  async function designScenesForChapter(pid: string, chapterOutline: Record<string, unknown>) {
    loading.value = true
    error.value = ''
    try {
      const r = await designScenes(pid, chapterOutline)
      scenes.value = r.scenes
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveSceneData(pid: string, sceneId: string, data: Record<string, unknown>) {
    return saveScene(pid, sceneId, data)
  }

  async function generatePlanning(pid: string) {
    loading.value = true
    try {
      await generateVolumeDetail(pid, 1, {} as MasterOutline)
      await generateNodes(pid, {} as ChapterPlan, {} as MasterOutline)
      await planChaptersForVolume(pid, {} as MasterOutline, [], 30000)
      await generateOutline(pid, 1, {} as ChapterPlan)
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

  function savePlanning(pid: string, data: Record<string, unknown>) {
    if (data.volumes) volumes.value = data.volumes as VolumeDetail[]
    if (data.plotNodes) plotNodes.value = data.plotNodes as PlotEventDetail[]
    if (data.chapterPlans) chapterPlans.value = data.chapterPlans as ChapterPlan[]
    if (data.chapterOutlines) chapterOutlines.value = data.chapterOutlines as ChapterOutline[]
  }

  return {
    projectId, volumes, plotNodes, chapterPlans, chapterOutlines, scenes, loading, error,
    generateVolumeDetail, saveVolumeDetail, generateNodes, saveNode,
    planChaptersForVolume, saveChapterPlanData, generateOutline, saveOutline,
    designScenesForChapter, saveSceneData, generatePlanning, savePlanning,
  }
})
