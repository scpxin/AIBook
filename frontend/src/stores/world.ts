import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WorldBuilding, WorldOrigin, WorldRule, WorldConsistencyCheck } from '../types/v2'
import {
  generateWorldOrigin, generateWorldRules, generateWorldStructure,
  generateWorldCivilization, generateWorldHistory, checkWorldConsistency, saveWorld,
} from '../api/v2'

export const useWorldStore = defineStore('world', () => {
  const projectId = ref('')
  const origin = ref<WorldOrigin | any>({})
  const rules = ref<WorldRule[]>([])
  const metaRule = ref('')
  const structure = ref<any>({})
  const civilization = ref<any>({})
  const history = ref<any>({})
  const consistencyCheck = ref<WorldConsistencyCheck | null>(null)
  const docPath = ref('')
  const loading = ref(false)
  const error = ref('')

  async function generateOrigin(pid: string, idea: string, genre?: string) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      origin.value = await generateWorldOrigin(pid, idea, genre)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateRules(pid: string, originData: any, powerSystem?: any) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateWorldRules(pid, originData, powerSystem)
      rules.value = r.rules
      metaRule.value = r.metaRule
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateStructure(pid: string, originData: any) {
    loading.value = true
    error.value = ''
    try {
      structure.value = await generateWorldStructure(pid, originData)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateCivilization(pid: string, structureData: any) {
    loading.value = true
    error.value = ''
    try {
      civilization.value = await generateWorldCivilization(pid, structureData)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateHistory(pid: string, structureData: any, civData: any) {
    loading.value = true
    error.value = ''
    try {
      history.value = await generateWorldHistory(pid, structureData, civData)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function checkConsistency(pid: string) {
    loading.value = true
    error.value = ''
    try {
      const worldData = { origin: origin.value, rules: rules.value, structure: structure.value, civilization: civilization.value, history: history.value }
      consistencyCheck.value = await checkWorldConsistency(pid, worldData)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function save(pid: string): Promise<any> {
    const worldData: WorldBuilding = {
      origin: origin.value, rules: rules.value, structure: structure.value,
      civilization: civilization.value, history: history.value, docPath: docPath.value,
    }
    return saveWorld(pid, worldData)
  }

  async function generateWorld(pid: string, origin: any, ideaText?: string, genre?: string, onProgress?: (step: number, msg: string) => void) {
    loading.value = true
    try {
      const idea = ideaText || origin.originStory || ''
      const gen = genre || origin.worldType || ''
      await generateOrigin(pid, idea, gen)
      onProgress?.(1, '正在生成世界规则...')
      await generateRules(pid, origin)
      onProgress?.(2, '正在生成世界结构...')
      await generateStructure(pid, origin)
      onProgress?.(3, '正在生成文明体系...')
      await generateCivilization(pid, origin)
      onProgress?.(4, '正在生成历史时间线...')
      await generateHistory(pid, origin, civilization.value)
      onProgress?.(5, '世界观生成完成')
      return {
        origin: origin.value, rules: rules.value,
        structure: structure.value, civilization: civilization.value, history: history.value,
      }
    } finally {
      loading.value = false
    }
  }

  function saveWorld(pid: string, data: any): Promise<any> {
    if (data.origin) Object.assign(origin.value, data.origin)
    if (data.rules) Object.assign(rules.value, data.rules)
    return save(pid)
  }

  return {
    projectId, origin, rules, metaRule, structure, civilization, history,
    consistencyCheck, docPath, loading, error,
    generateOrigin, generateRules, generateStructure, generateCivilization,
    generateHistory, checkConsistency, save, generateWorld, saveWorld,
  }
})
