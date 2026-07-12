import { ref, computed } from 'vue'
import {
  apiGet, apiPost, apiPut, apiDelete,
} from '../api/client'

// 类型定义
export interface GenerationTemplate {
  id: number
  name: string
  module_key: string
  genre: string
  sub_genre: string
  tone: string
  world_type: string
  target_audience: string
  source_project_id: string
  input_fingerprint: string
  output_data: any
  input_context: any
  entity_refs: any
  compatibility_group: string
  usage_count: number
  quality_rating: number
  is_public: number
  created_at: string
  updated_at: string
}

export interface MatchResult {
  template: GenerationTemplate
  score: number
  is_compatible: boolean
  reason?: string
}

export interface ProjectSharedContext {
  worldType: string
  locations: string[]
  factions: string[]
  characters: string[]
  powerSystem: string
  plotNodes: string[]
  genre: string
  subGenre: string
  tone: string
  targetAudience: string
}

// 单例状态
const allTemplates = ref<GenerationTemplate[]>([])
const projectSharedContexts = ref<Record<string, ProjectSharedContext>>({})
const currentContextProjectId = ref<string>('')
const loading = ref(false)
const error = ref('')

function getContext(projectId: string): ProjectSharedContext {
  if (!projectSharedContexts.value[projectId]) {
    projectSharedContexts.value[projectId] = {
      worldType: '',
      locations: [],
      factions: [],
      characters: [],
      powerSystem: '',
      plotNodes: [],
      genre: '',
      subGenre: '',
      tone: '',
      targetAudience: '',
    }
  }
  return projectSharedContexts.value[projectId]
}

export function useTemplateStore() {
  async function fetchTemplates(filter: {
    module_key?: string
    genre?: string
    world_type?: string
    limit?: number
  } = {}) {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string> = {}
      if (filter.module_key) params.module_key = filter.module_key
      if (filter.genre) params.genre = filter.genre
      if (filter.world_type) params.world_type = filter.world_type
      if (filter.limit) params.limit = String(filter.limit)
      const res = await apiGet<{ templates: GenerationTemplate[] }>('/api/v2/generation-templates/', params)
      allTemplates.value = res.templates || []
      return allTemplates.value
    } catch (e: any) {
      error.value = e.message || '获取模板失败'
      return []
    } finally {
      loading.value = false
    }
  }

  async function getTemplate(id: number): Promise<GenerationTemplate | null> {
    try {
      const res = await apiGet<{ template: GenerationTemplate }>(`/api/v2/generation-templates/${id}`)
      return res.template
    } catch {
      return null
    }
  }

  async function createTemplate(data: {
    name: string
    module_key: string
    output_data: any
    input_context?: any
    genre?: string
    sub_genre?: string
    tone?: string
    world_type?: string
    target_audience?: string
    is_public?: boolean
  }) {
    const res = await apiPost<{ ok: boolean; template: GenerationTemplate }>(
      '/api/v2/generation-templates/',
      data
    )
    if (res.ok && res.template) {
      allTemplates.value.unshift(res.template)
    }
    return res.template
  }

  async function updateTemplate(id: number, data: Partial<{
    name: string
    genre: string
    sub_genre: string
    tone: string
    world_type: string
    target_audience: string
    quality_rating: number
    is_public: boolean
  }>) {
    const res = await apiPut<{ ok: boolean; template: GenerationTemplate }>(
      `/api/v2/generation-templates/${id}`,
      data
    )
    if (res.ok && res.template) {
      const idx = allTemplates.value.findIndex(t => t.id === id)
      if (idx >= 0) allTemplates.value[idx] = res.template
    }
    return res.template
  }

  async function deleteTemplate(id: number) {
    const res = await apiDelete<{ ok: boolean }>(`/api/v2/generation-templates/${id}`)
    if (res.ok) {
      allTemplates.value = allTemplates.value.filter(t => t.id !== id)
    }
    return res.ok
  }

  async function matchTemplates(moduleKey: string, projectContext: Record<string, string>, selectedTemplates: Record<string, string>) {
    try {
      const res = await apiPost<{
        compatible: MatchResult[]
        incompatible: MatchResult[]
        total_candidates: number
      }>('/api/v2/generation-templates/match', {
        module_key: moduleKey,
        project_context: projectContext,
        selected_templates: selectedTemplates,
      })
      return res
    } catch {
      return { compatible: [], incompatible: [], total_candidates: 0 }
    }
  }

  async function applyTemplate(templateId: number, projectId: string) {
    const res = await apiPost<{
      success: boolean
      module: string
      data: any
      applied_as: string
    }>(`/api/v2/generation-templates/${templateId}/apply`, {
      project_id: projectId,
    })
    return res
  }

  async function rateTemplate(id: number, rating: number) {
    return apiPost<{ ok: boolean }>(`/api/v2/generation-templates/${id}/rate`, { rating })
  }

  async function autoSaveTemplate(data: {
    project_id: string
    module_key: string
    module_data: any
    input_context?: any
    compatibility_group?: string
  }) {
    try {
      const res = await apiPost('/api/v2/generation-templates/auto-save', data)
      return res
    } catch {
      return { ok: false, auto_saved: false }
    }
  }

  async function getCompatGroup(groupId: string) {
    try {
      const res = await apiGet<{ templates: GenerationTemplate[] }>(
        `/api/v2/generation-templates/compat-group/${groupId}`
      )
      return res.templates || []
    } catch {
      return []
    }
  }

  async function getProjectTemplates(projectId: string) {
    try {
      const res = await apiGet<{ templates: GenerationTemplate[] }>(
        `/api/v2/generation-templates/project/${projectId}`
      )
      return res.templates || []
    } catch {
      return []
    }
  }

  function updateSharedContext(moduleKey: string, outputData: any, projectId: string = '') {
    const ctx = getContext(projectId)
    if (!outputData || typeof outputData !== 'object') return

    if (moduleKey === 'world') {
      const wb = outputData.world_building || outputData
      if (wb.world_type || wb.worldType) {
        ctx.worldType = wb.world_type || wb.worldType
      }
      if (wb.locations || wb.territories) {
        const locs = wb.locations || wb.territories
        ctx.locations = typeof locs === 'string'
          ? locs.split('\n').filter(Boolean)
          : Array.isArray(locs) ? locs : []
      }
      if (wb.factions_races || wb.races) {
        const facs = wb.factions_races || wb.races
        ctx.factions = typeof facs === 'string'
          ? facs.split('\n').filter(Boolean)
          : Array.isArray(facs) ? facs : []
      }
    }

    if (moduleKey === 'characters') {
      const chars: string[] = []
      for (const role of ['protagonist', 'supporting', 'villains', 'antagonists']) {
        let items = outputData[role]
        if (typeof items === 'object' && !Array.isArray(items)) items = [items]
        if (Array.isArray(items)) {
          for (const c of items) {
            if (c && c.name) chars.push(c.name)
          }
        }
      }
      if (chars.length) ctx.characters = chars
    }

    if (moduleKey === 'factions') {
      const facs = outputData.factions
      if (Array.isArray(facs)) {
        ctx.factions = facs
          .filter((f: any) => f && f.name)
          .map((f: any) => f.name)
      }
    }

    if (moduleKey === 'power_system') {
      if (outputData.system_type || outputData.systemType) {
        ctx.powerSystem = outputData.system_type || outputData.systemType
      }
    }

    if (moduleKey === 'story_architecture') {
      const nodes = outputData.plot_nodes || outputData.key_events
      if (Array.isArray(nodes)) {
        ctx.plotNodes = nodes
          .map((p: any) => (typeof p === 'object' ? (p.name || p.event) : p))
          .filter(Boolean) as string[]
      }
    }
  }

  function resetSharedContext(projectId: string = '') {
    projectSharedContexts.value[projectId] = {
      worldType: '',
      locations: [],
      factions: [],
      characters: [],
      powerSystem: '',
      plotNodes: [],
      genre: '',
      subGenre: '',
      tone: '',
      targetAudience: '',
    }
  }

  function activateProject(projectId: string) {
    currentContextProjectId.value = projectId
    getContext(projectId)
  }

  const templatesByModule = computed(() => {
    const map: Record<string, GenerationTemplate[]> = {}
    for (const t of allTemplates.value) {
      if (!map[t.module_key]) map[t.module_key] = []
      map[t.module_key].push(t)
    }
    return map
  })

  const sharedContext = computed(() => getContext(currentContextProjectId.value))

  return {
    // state
    allTemplates,
    loading,
    error,
    templatesByModule,
    sharedContext,
    // actions
    fetchTemplates,
    getTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    matchTemplates,
    applyTemplate,
    rateTemplate,
    autoSaveTemplate,
    getCompatGroup,
    getProjectTemplates,
    updateSharedContext,
    resetSharedContext,
    activateProject,
  }
}
