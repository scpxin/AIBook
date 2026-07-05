// @ts-nocheck
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { IdeaCandidate, IdeaScore, IdeaUpgrade, RiskAnalysis } from '../types/v2'
import { generateIdeas, scoreIdeas, upgradeIdeas, analyzeIdeaRisks } from '../api/v2'

export const useIdeaStore = defineStore('idea', () => {
  const projectId = ref('')
  const ideas = ref<IdeaCandidate[]>([])
  const selectedIdea = ref<IdeaCandidate | null>(null)
  const scores = ref<IdeaScore[]>([])
  const upgradeVersions = ref<IdeaUpgrade[]>([])
  const risks = ref<RiskAnalysis | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function generate(pid: string, userInput: string, genreHint?: string, count?: number) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      const r = await generateIdeas(pid, userInput, genreHint, count)
      ideas.value = r.ideas
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function score(pid: string, ideaList?: IdeaCandidate[]) {
    loading.value = true
    error.value = ''
    try {
      const r = await scoreIdeas(pid, ideaList || ideas.value)
      scores.value = r.scoredIdeas
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function upgrade(pid: string, topIdeas?: IdeaCandidate[]) {
    loading.value = true
    error.value = ''
    try {
      const r = await upgradeIdeas(pid, topIdeas || ideas.value.slice(0, 3))
      upgradeVersions.value = r.upgraded
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function analyzeRisks(pid: string, concept: string) {
    loading.value = true
    error.value = ''
    try {
      risks.value = await analyzeIdeaRisks(pid, concept)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function select(idea: IdeaCandidate) {
    selectedIdea.value = idea
  }

  async function generateIdeas(pid: string, prompt: string, genre?: string) {
    await generate(pid, prompt, genre)
    return { candidates: ideas.value }
  }

  async function upgradeIdea(candidate: any) {
    const pid = projectId.value
    return upgrade(pid, [candidate])
  }

  return {
    projectId, ideas, selectedIdea, scores, upgradeVersions, risks, loading, error,
    generate, score, upgrade, analyzeRisks, select, generateIdeas, upgradeIdea,
  }
})
