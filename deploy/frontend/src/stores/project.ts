import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '../api/client'
import * as projectApi from '../api/project'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref('')
  const selectedProjectId = ref('')
  const projectName = ref('')
  const projectList = ref<Project[]>([])

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

  async function save(data: { id?: string; name: string; step: number; novelData: any }) {
    const r = await projectApi.saveProjectApi({
      id: data.id,
      name: data.name,
      step: data.step,
      data: data.novelData,
      tags: '',
    })
    currentProjectId.value = r.id
    selectedProjectId.value = r.id
    return r
  }

  async function load(id: string) {
    return projectApi.loadProjectApi(id)
  }

  async function remove(id: string) {
    await projectApi.deleteProjectApi(id)
    if (currentProjectId.value === id) {
      currentProjectId.value = ''
      projectName.value = ''
    }
    selectedProjectId.value = ''
    await loadList()
  }

  const v2PipelineId = ref('')
  const isV2Project = ref(false)

  async function saveV2(data: { id?: string; name: string; pipelineData: any }) {
    const r = await projectApi.saveProjectApi({
      id: data.id,
      name: data.name,
      step: 0,
      data: { v2: true, pipeline: data.pipelineData },
      tags: 'v2',
    })
    currentProjectId.value = r.id
    selectedProjectId.value = r.id
    v2PipelineId.value = r.id
    isV2Project.value = true
    return r
  }

  function setV2Project(v2: boolean, pipelineId?: string) {
    isV2Project.value = v2
    if (pipelineId) v2PipelineId.value = pipelineId
  }

  return {
    currentProjectId,
    selectedProjectId,
    projectName,
    projectList,
    v2PipelineId,
    isV2Project,
    loadList,
    save,
    saveV2,
    load,
    remove,
    setV2Project,
  }
})
