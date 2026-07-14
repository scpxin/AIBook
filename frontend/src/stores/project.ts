import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '../api/client'
import * as projectApi from '../api/project'

export interface V2ProjectData {
  id?: string
  name: string
  modules?: Record<string, any>
  pipeline: any
  templateSelections?: Record<string, string>
  sharedContext?: Record<string, any>
  updatedAt?: string
}

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref('')
  const selectedProjectId = ref('')
  const projectName = ref('')
  const projectList = ref<Project[]>([])
  const v2ProjectMeta = ref<Record<string, any>>({})
  const projectUpdatedAt = ref<string>('')

  async function loadList() {
    try {
      const r = await projectApi.listProjectsApi()
      projectList.value = (r.projects || []).map(p => ({
        id: p.id,
        name: p.name,
        step: p.step,
        updated_at: p.updated_at,
        tags: p.tags,
      }))
    } catch {
      projectList.value = []
    }
  }

  async function remove(id: string) {
    await projectApi.softDeleteV2Project(id)
    if (currentProjectId.value === id) {
      currentProjectId.value = ''
      projectName.value = ''
    }
    selectedProjectId.value = ''
    await loadList()
  }

  /**
   * 全量保存V2项目：收集所有模块数据 + 流水线状态 + 模板选择 + 共享上下文
   */
  async function saveV2Full(data: V2ProjectData) {
    const r = await projectApi.saveV2Project({
      id: data.id,
      name: data.name,
      modules: data.modules || {},
      pipeline: data.pipeline,
      templateSelections: data.templateSelections || {},
      sharedContext: data.sharedContext || {},
      expectedUpdatedAt: projectUpdatedAt.value,
    })
    currentProjectId.value = r.id
    selectedProjectId.value = r.id
    if (r.updated_at) projectUpdatedAt.value = r.updated_at
    if (!data.id) {
      await loadList()
    }
    return r
  }

  /**
   * 加载V2项目全量数据
   */
  async function loadV2Full(id: string): Promise<V2ProjectData> {
    const data = await projectApi.loadV2Project(id)
    currentProjectId.value = data.id
    selectedProjectId.value = data.id
    projectName.value = data.name
    projectUpdatedAt.value = data.updated_at || ''
    v2ProjectMeta.value = {
      templateSelections: data.templateSelections || {},
      sharedContext: data.sharedContext || {},
    }
    return data
  }

  return {
    currentProjectId,
    selectedProjectId,
    projectName,
    projectList,
    v2ProjectMeta,
    projectUpdatedAt,
    loadList,
    remove,
    saveV2Full,
    loadV2Full,
  }
})
