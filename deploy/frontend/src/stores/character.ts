import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Character, RelationMap, CharacterConsistencyCheck } from '../types/v2'
import {
  generateProtagonist, generateSupporting, generateAntagonists,
  generateRelations, checkCharacterConsistency,
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
      protagonist.value = await generateProtagonist(pid, worldRules, storyConcept)
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

  async function generateCharacters(pid: string) {
    loading.value = true
    try {
      await generateProtagonistProfile(pid, {} as any)
      await generateSupportingChars(pid, 3)
      await generateAntagonistsList(pid, {} as any)
      await buildRelationMap(pid)
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

  function saveCharacters(_pid: string, data: any) {
    if (data.protagonist && protagonist.value) Object.assign(protagonist.value, data.protagonist)
    if (data.supporting) supporting.value = data.supporting
    if (data.villains) antagonists.value = data.villains
  }

  return {
    projectId, protagonist, supporting, antagonists, relationMap, consistency, loading, error,
    generateProtagonistProfile, generateSupportingChars, generateAntagonistsList,
    buildRelationMap, checkConsistency, generateCharacters, saveCharacters,
  }
})
