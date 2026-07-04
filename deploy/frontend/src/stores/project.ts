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

  return {
    currentProjectId,
    selectedProjectId,
    projectName,
    projectList,
    loadList,
    save,
    load,
    remove,
  }
})
