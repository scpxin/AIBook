import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WorldBuilding, WorldOrigin, WorldRule, WorldConsistencyCheck, PowerSystem, WorldStructure, CivilizationDimension } from '../types/v2'
import {
  generateWorldOrigin, generateWorldRules, generateWorldStructure,
  generateWorldCivilization, generateWorldHistory, checkWorldConsistency, saveWorld,
  saveModuleData,
} from '../api/v2'


export const useWorldStore = defineStore('world', () => {
  const projectId = ref('')
  const origin = ref<WorldOrigin | any>({})
  const rules = ref<WorldRule[]>([])
  const metaRule = ref('')
  const structure = ref<WorldStructure>({})
  const civilization = ref<CivilizationDimension>({} as CivilizationDimension)
  const history = ref<Record<string, unknown>>({})
  const consistencyCheck = ref<WorldConsistencyCheck | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function generateOrigin(pid: string, idea: string, genre?: string) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      origin.value = await generateWorldOrigin(pid, idea, genre)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function generateRules(pid: string, originData: WorldOrigin, powerSystem?: PowerSystem) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateWorldRules(pid, originData, powerSystem)
      rules.value = r.rules
      metaRule.value = r.metaRule
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function generateStructure(pid: string, originData: WorldOrigin) {
    loading.value = true
    error.value = ''
    try {
      structure.value = await generateWorldStructure(pid, originData)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function generateCivilization(pid: string, structureData: WorldStructure) {
    loading.value = true
    error.value = ''
    try {
      civilization.value = await generateWorldCivilization(pid, structureData)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function generateHistory(pid: string, structureData: WorldStructure, civData: CivilizationDimension) {
    loading.value = true
    error.value = ''
    try {
      history.value = await generateWorldHistory(pid, structureData, civData)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
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
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function save(pid: string): Promise<any> {
    const worldData: WorldBuilding = {
      origin: origin.value, rules: rules.value, structure: structure.value,
      civilization: civilization.value, history: history.value,
    }
    await saveWorld(pid, worldData)
    await saveModuleData(pid, 'world', { ...worldData })
    return { saved: true }
  }

  async function generateWorld(pid: string, originInput: Record<string, unknown>, ideaText?: string, genre?: string, onProgress?: (step: number, msg: string) => void) {
    loading.value = true
    try {
      const idea = ideaText || String(originInput.originStory || '')
      const gen = genre || String(originInput.worldType || '')
      await generateOrigin(pid, idea, gen)
      const freshOrigin = origin.value
      onProgress?.(1, '正在生成世界规则...')
      await generateRules(pid, freshOrigin)
      onProgress?.(2, '正在生成世界结构...')
      await generateStructure(pid, freshOrigin)
      const freshStructure = structure.value
      onProgress?.(3, '正在生成文明体系...')
      await generateCivilization(pid, freshStructure)
      onProgress?.(4, '正在生成历史时间线...')
      await generateHistory(pid, freshStructure, civilization.value)
      onProgress?.(5, '世界观生成完成')
      const normalizedRules = Array.isArray(rules.value) ? rules.value.reduce((acc: Record<string, unknown>, r: Record<string, unknown>, i: number) => {
        const key = r.name === '力量体系' ? 'power' : r.name === '经济系统' ? 'economy' : r.name === '政治结构' ? 'politics' : r.name === '科技水平' ? 'technology' : r.name === '文化习俗' ? 'culture' : r.name === '禁忌规则' ? 'taboo' : `rule${i}`
        acc[key] = r.description || ''
        return acc
      }, {}) : rules.value
      const normalizedHistory = (() => {
        const raw = history.value
        if (Array.isArray(raw)) return raw as unknown[]
        if (raw && raw.history && Array.isArray(raw.history)) return raw.history as unknown[]
        if (typeof raw === 'object' && raw !== null) return Object.entries(raw).map(([k, v]) => ({ era: k, description: String(v) }))
        return []
      })()
      return {
        origin: origin.value, rules: normalizedRules,
        structure: structure.value, civilization: civilization.value, history: normalizedHistory,
      }
    } finally {
      loading.value = false
    }
  }

  function updateLocalWorld(pid: string, data: Record<string, unknown>): Promise<any> {
    if (data.origin) Object.assign(origin.value, data.origin)
    if (data.rules) Object.assign(rules.value, data.rules)
    return save(pid)
  }

  return {
    projectId, origin, rules, metaRule, structure, civilization, history,
    consistencyCheck, loading, error,
    generateOrigin, generateRules, generateStructure, generateCivilization,
    generateHistory, checkConsistency, save, generateWorld,
    saveWorldToBackend: saveWorld, updateLocalWorld,
  }
})
