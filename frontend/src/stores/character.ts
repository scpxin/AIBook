import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Character, RelationMap, CharacterConsistencyCheck } from '../types/v2'
import {
  generateProtagonist, generateSupporting, generateAntagonists,
  generateRelations, checkCharacterConsistency, saveModuleData,
} from '../api/v2'

export const useCharacterStore = defineStore('character', () => {
  const projectId = ref('')
  const protagonist = ref<Character | null>(null)
  const supporting = ref<Character[]>([])
  const antagonists = ref<Character[]>([])
  const relationMap = ref<RelationMap | null>(null)
  const consistency = ref<CharacterConsistencyCheck | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function generateProtagonistProfile(pid: string, worldRules: any, storyConcept?: string) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      const result = await generateProtagonist(pid, worldRules, storyConcept)
      if (result && !result.name && result.basic_info) {
        const bi = result.basic_info
        protagonist.value = {
          name: bi.name || '',
          gender: bi.gender || '',
          age: bi.age || '',
          appearance: bi.appearance || '',
          personality: Array.isArray(result.personality?.traits) ? result.personality.traits.join(',') : (result.personality?.traits || ''),
          background: result.backstory?.origin || '',
          goal: result.motivation?.outer_goal || '',
          flaw: Array.isArray(result.personality?.flaws) ? result.personality.flaws.join(',') : (result.personality?.flaws || ''),
          arc: result.character_arc?.final_state || '',
          ...result,
        }
      } else {
        protagonist.value = result
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateSupportingChars(pid: string, count?: number) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateSupporting(pid, protagonist.value, count)
      supporting.value = r.characters
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateAntagonistsList(pid: string, world: any) {
    loading.value = true
    error.value = ''
    try {
      const r = await generateAntagonists(pid, protagonist.value, world)
      antagonists.value = (r as any).antagonists || []
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function buildRelationMap(pid: string) {
    loading.value = true
    error.value = ''
    try {
      const allChars = [protagonist.value, ...supporting.value].filter(Boolean) as Character[]
      relationMap.value = await generateRelations(pid, allChars)
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
      const allChars = [protagonist.value, ...supporting.value, ...antagonists.value].filter(Boolean) as Character[]
      consistency.value = await checkCharacterConsistency(pid, allChars)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateCharacters(pid: string, worldData?: any, storyConcept?: string, onProgress?: (step: number, msg: string) => void) {
    loading.value = true
    try {
      await generateProtagonistProfile(pid, worldData?.rules || worldData || {}, storyConcept)
      onProgress?.(1, '正在生成配角...')
      await generateSupportingChars(pid, 3)
      onProgress?.(2, '正在生成反派体系...')
      await generateAntagonistsList(pid, worldData || {})
      onProgress?.(3, '正在生成角色关系...')
      await buildRelationMap(pid)
      onProgress?.(4, '角色生成完成')
      return {
        protagonist: protagonist.value,
        supporting: supporting.value,
        villains: antagonists.value,
        relations: relationMap.value,
      }
    } finally {
      loading.value = false
    }
  }

  async function saveCharacters(pid: string, data: any) {
    if (data.protagonist && protagonist.value) Object.assign(protagonist.value, data.protagonist)
    if (data.supporting) supporting.value = data.supporting
    if (data.villains) antagonists.value = data.villains
    if (data.relations) relationMap.value = data.relations
    await saveModuleData(pid, 'characters', {
      protagonist: protagonist.value,
      supporting: supporting.value,
      villains: antagonists.value,
      relations: relationMap.value,
    })
  }

  return {
    projectId, protagonist, supporting, antagonists, relationMap, consistency, loading, error,
    generateProtagonistProfile, generateSupportingChars, generateAntagonistsList,
    buildRelationMap, checkConsistency, generateCharacters, saveCharacters,
  }
})
