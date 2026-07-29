import { type Ref } from 'vue'
import { loadV2Project } from '../api/project'
import type { ModuleInfo } from '../types/v2'
import type { Project } from '../api/client'
import logger from '../utils/logger'

interface UseV2InitParams {
  projectId: Ref<string>
  projectName: Ref<string>
  modules: Ref<ModuleInfo[]>
  existingProjects: Ref<Project[]>
  pageLoading: Ref<boolean>
  modulesLoadError: Ref<string>
  restoreNotice: Ref<string>
  allModulesData: Ref<Record<string, any>>
  currentProjectGenre: Ref<string>
  currentProjectAudience: Ref<string>
  currentProjectSubGenre: Ref<string>
  currentProjectTone: Ref<string>
  showOnboarding: Ref<boolean>
  pendingModuleData: Ref<Record<string, any>>
  moduleSavedMap: Ref<Record<string, boolean>>
  selectedTemplateModules: Ref<Record<string, string>>
  pipeline: any
  projectStore: any
  tplStore: any
  toast: any
  route: any
  currentModule: any
  generateId: () => string
  handleBeforeUnload: (e: BeforeUnloadEvent) => void
  _isNewProject: boolean
}

export function useV2Init(params: UseV2InitParams) {
  const {
    projectId, projectName, modules, existingProjects, pageLoading, modulesLoadError,
    restoreNotice, allModulesData, currentProjectGenre, currentProjectAudience,
    currentProjectSubGenre, currentProjectTone, showOnboarding,
    pendingModuleData, moduleSavedMap, selectedTemplateModules,
    pipeline, projectStore, tplStore, toast, route, currentModule, generateId,
    handleBeforeUnload, _isNewProject,
  } = params

  async function init() {
    pageLoading.value = true
    try {
      await pipeline.loadModules()
    } catch (e: any) {
      modulesLoadError.value = e?.message || '加载模块列表失败'
      pageLoading.value = false
      return
    }
    modules.value = pipeline.modules
    if (!projectId.value) {
      projectId.value = generateId()
      projectName.value = '我的小说'
    }
    await pipeline.loadStatus(projectId.value)
    tplStore.activateProject(projectId.value)

    const doneCount = Object.values(pipeline.progress?.modules || {}).filter((m: any) => m.status === 'done').length
    if (doneCount > 0) {
      restoreNotice.value = `已从上次进度恢复：已完成 ${doneCount} / ${modules.value.length} 个模块（当前：${pipeline.currentModule}）`
    }

    try {
      if (!projectStore.projectList || projectStore.projectList.length === 0) {
        await projectStore.loadList()
      }
      existingProjects.value = projectStore.projectList || []
    } catch (_e) {
      logger.error('[CreateV2] preload existing projects failed:', _e)
    }

    try {
      const v2Data = await loadV2Project(projectId.value)
      projectName.value = v2Data?.name || projectName.value || '未命名项目'
      allModulesData.value = v2Data?.modules || {}
      if (!v2Data?.name && (!projectName.value || projectName.value === '我的小说V2' || projectName.value === '我的小说' || projectName.value === '新项目')) {
        const ida = v2Data?.modules?.['idea']
        if (ida) {
          const sel = ida.confirmedCandidate || (ida.selectedIdx != null ? ida.candidates?.[ida.selectedIdx] : null)
          if (sel?.title || sel?.concept) {
            projectName.value = (sel.title || sel.concept || '').slice(0, 64)
          }
        }
      }
      const ideaData = v2Data?.modules?.['idea']
      if (ideaData) {
        currentProjectGenre.value = ideaData.genre || ideaData.genreHint || ''
        currentProjectAudience.value = ideaData.target_audience || ''
      }
      const projData = v2Data?.modules?.['project']
      if (projData) {
        currentProjectSubGenre.value = projData.sub_genre || projData.subGenre || ''
        currentProjectTone.value = projData.tone || projData.style || ''
      }
      const worldData = v2Data?.modules?.['world']
      if (worldData) {
        const wbData = worldData.world_building || worldData
        tplStore.updateSharedContext('world', {
          world_type: wbData.world_type || wbData.worldType || '',
          locations: wbData.locations || wbData.territories || [],
        }, projectId.value)
      }
      const charData = v2Data?.modules?.['characters']
      if (charData) tplStore.updateSharedContext('characters', charData, projectId.value)
      const facData = v2Data?.modules?.['world']?.factions
      if (facData) tplStore.updateSharedContext('factions', facData, projectId.value)
    } catch (_e) {
      logger.error('[CreateV2] restore module data failed:', _e)
    }

    const hasSeenOnboarding = localStorage.getItem('onboarding_seen_v2')
    const hasExistingProgress = Object.values(pipeline.progress?.modules || {}).some((m: any) => m.status === 'done')
    if (!hasSeenOnboarding && !hasExistingProgress) {
      showOnboarding.value = true
      localStorage.setItem('onboarding_seen_v2', '1')
    }

    if (_isNewProject && !route.query.name && projectName.value === '新项目') {
      const name = window.prompt('请输入项目名称：', '')
      if (name && name.trim()) {
        projectName.value = name.trim().slice(0, 64)
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    const applyTemplateId = route.query.applyTemplate as string
    if (applyTemplateId) {
      try {
        const tpl = await tplStore.getTemplate(Number(applyTemplateId))
        if (tpl && tpl.output_data) {
          pendingModuleData.value[currentModule.value] = tpl.output_data
          moduleSavedMap.value[currentModule.value] = true
          selectedTemplateModules.value[currentModule.value] = String(tpl.id)
          tplStore.updateSharedContext(tpl.module_key, tpl.output_data, projectId.value)
          toast.success(`已应用模板: ${tpl.name}`)
        }
      } catch (_e) {
        logger.error('[CreateV2] applyTemplate failed:', _e)
        toast.error('应用模板失败')
      }
    }

    pageLoading.value = false
  }

  return { init }
}
