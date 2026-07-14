<template>
  <div class="create-v2">
    <AppConfirmDialog />
    <AppErrorBar />
    <GenerationStatusBar />
    <div v-if="pageLoading" class="page-loading-full">
      <div class="loading-spinner"></div>
      <p>正在初始化创作流程...</p>
    </div>
    <div v-else-if="modulesLoadError" class="error-page"><h3>创作流程加载失败</h3><p>{{ modulesLoadError }}</p><button @click="reloadPage" class="btn-primary">重试</button></div>
    <div v-else style="display:flex;flex-direction:column;flex:1;min-height:0">
    <div v-if="!isOnline" class="offline-banner">
      <span>📡 网络已断开 — 仍可查看和编辑已保存内容，模板复用功能离线可用</span>
    </div>
    <div v-if="showAIGuard" class="ai-guard-banner">
      <span>请先配置大模型API后才能使用AI生成功能</span>
      <button @click="openSettings" class="btn-config-ai">立即配置</button>
    </div>
    <div class="v2-header">
      <h2>AI创作V2 — 19模块流水线</h2>
      <div class="header-actions">
        <button @click="goToProjects" class="btn-projects" title="管理所有项目">
          📚 项目
        </button>
        <button @click="handleNewProject" class="btn-new-project" title="新建项目">
          + 新建
        </button>
        <select v-model="projectId" @change="switchProject" class="project-select">
          <option :value="projectId">{{ projectName || '当前项目' }}</option>
          <option v-for="p in existingProjects.filter(p => p.id !== projectId)" :key="p.id" :value="p.id">
            {{ p.name || '未命名项目' }}（{{ formatProjectDate(p.updated_at) }}）
          </option>
        </select>
        <input v-model="projectName" placeholder="项目名称" class="project-name-input" maxlength="64" @input="validateProjectName" />
        <span v-if="projectNameError" class="project-name-error">{{ projectNameError }}</span>
        <button @click="saveCurrentModule" :disabled="!hasUnsavedChanges() || isSavingModule()" class="btn btn-save-module" title="保存当前模块到数据库">
          <span v-if="isSavingModule()" class="btn-spinner"></span>
          <span v-else>保存当前模块</span>
        </button>
        <button @click="saveProjectFull" :disabled="saving" class="btn-save" title="保存所有模块数据">
          <span v-if="saving" class="btn-spinner"></span>
          <span v-else-if="saveSuccess" class="save-toast">已保存!</span>
          <span v-else>保存项目</span>
        </button>
        <button @click="showExport = !showExport" class="btn-export">导出</button>
        <button @click="showOnboarding = true" class="btn-help">查看引导</button>
        <button
          v-if="templateSupportedModules.includes(currentModule)"
          @click="openTemplateSelector"
          class="btn-template"
          title="从模板选择，不消耗token"
        >
          📋 模板
        </button>
        <button @click="goToTemplates" class="btn-template" title="管理模板库" style="text-decoration:none">
          📚 模板库
        </button>
      </div>
    </div>

    <TemplateSelector
      v-if="showTemplateSelector"
      :module-key="currentModule"
      :module-display-name="currentModuleInfo?.display_name || currentModule"
      :project-id="projectId"
      :project-context="projectContextForTemplate"
      :selected-templates="selectedTemplateModules"
      @close="showTemplateSelector = false"
      @select-a-i="handleTemplateSelectAI"
      @select-template="handleTemplateApply"
    />

    <SaveAsTemplate
      v-if="showSaveAsTemplate"
      :project-id="projectId"
      :module-key="currentModule"
      :module-data="currentTemplateData"
      :input-context="currentTemplateInputCtx"
      :suggested-name="`${projectContextForTemplate.genre}-${currentModuleInfo?.display_name || currentModule}`"
      @close="showSaveAsTemplate = false"
      @saved="handleTemplateSaved"
    />

    <div v-if="showExport" class="export-panel">
      <ExportView :project-id="projectId" />
    </div>
    <OnboardingGuide v-model="showOnboarding" />

    <div v-if="restoreNotice" class="restore-notice">
      &#10003; {{ restoreNotice }}
      <button @click="restoreNotice = ''" class="btn-dismiss">&times;</button>
    </div>

    <div class="v2-layout">
      <ModuleProgressSidebar
        :modules="modules"
        :current-module="currentModule"
        :progress-pct="progressPct"
        :stats="sidebarStats"
        :dependency-states="moduleDependencyStates"
        @select="goToModule"
      />

      <div class="v2-main">
        <div class="module-nav">
          <button @click="prevModule" :disabled="!canGoPrev" class="btn-nav">← 上一步</button>
          <span class="module-title">
            {{ currentModuleInfo?.display_name || currentModule }}
            <span v-if="moduleSavedMap[currentModule]" class="save-badge">已保存</span>
          </span>
          <button @click="skipModule" :disabled="!canGoNext || nonSkippableModules.includes(currentModule)" class="btn-nav btn-skip" title="跳过当前模块">跳过</button>
          <button @click="completeAndNext" :disabled="!canGoNext || !hasModuleData || completing" class="btn-nav btn-next">下一步 →</button>
        </div>

        <div class="module-content">
          <Transition name="module-fade" mode="out-in">
            <IdeaView v-if="currentModule === 'idea'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <ProjectView v-else-if="currentModule === 'project'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <WorldView v-else-if="currentModule === 'world'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <CharacterView v-else-if="currentModule === 'characters'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <StoryArchitectureView v-else-if="currentModule === 'story_architecture'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <TimelineView v-else-if="currentModule === 'timeline'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <OutlineView v-else-if="currentModule === 'outline'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
<PowerSystemView v-else-if="currentModule === 'power_system'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" @skip="onModuleComplete" />
<FactionsView v-else-if="currentModule === 'factions'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" @skip="onModuleComplete" />
            <PlanningView v-else-if="['volumes', 'chapter_plan', 'chapter_outline'].includes(currentModule)" :key="currentModule + projectId" :project-id="projectId" :current-module="currentModule" @complete="onModuleComplete" />
            <SceneDesignView v-else-if="currentModule === 'scene_design'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <DraftInlineView v-else-if="currentModule === 'draft_generation'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <ContentView v-else-if="currentModule === 'content_parsing'" :key="currentModule + '_cp' + projectId" :project-id="projectId" module-type="content_parsing" title="内容解析" desc="对正文进行结构化解析，提取场景、对白、情绪等要素" action-label="解析内容" @complete="onModuleComplete" />
            <ContentView v-else-if="currentModule === 'polish'" :key="currentModule + '_pl' + projectId" :project-id="projectId" module-type="polish" title="润色优化" desc="对正文进行AI润色，提升文采、修正语病、增强表现力" action-label="开始润色" @complete="onModuleComplete" />
            <ContentView v-else-if="currentModule === 'knowledge_update'" :key="currentModule + '_ku' + projectId" :project-id="projectId" module-type="knowledge_update" title="知识库更新" desc="根据正文内容自动更新角色状态、世界状态、剧情状态" action-label="更新知识库" @complete="onModuleComplete" />
            <ContentView v-else-if="currentModule === 'consistency_check'" :key="currentModule + '_cc' + projectId" :project-id="projectId" module-type="consistency_check" title="一致性检查" desc="检查正文与前期设定的矛盾冲突：人物、世界观、剧情连贯性" action-label="运行检查" @complete="onModuleComplete" />
            <div v-else class="module-placeholder" :key="currentModule">
              <h3>{{ currentModuleInfo?.display_name || currentModule }}</h3>
              <p>该模块视图正在建设中...</p>
              <button @click="onModuleComplete(currentModule)" class="btn-skip">跳过此模块</button>
            </div>
          </Transition>
        </div>
      </div>

      <div class="v2-side-panel">
        <KnowledgePanel :project-id="projectId" />
        <ForeshadowPanel :project-id="projectId" />
        <ConsistencyPanel :project-id="projectId" />
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, provide } from 'vue'
import { useNetworkStatus } from '../composables/useNetworkStatus'
import { flushAllSaves } from '../composables/useSaveRegistry'
import { useModuleSaveStore } from '../stores/moduleSave'
import { useRoute, useRouter } from 'vue-router'
import { usePipelineStore } from '../stores/pipeline'
import { useProjectStore } from '../stores/project'
import { generateId } from '../utils'
import { saveModuleData, getAllModuleData, updateModuleStatus } from '../api/v2'
import { loadV2Project } from '../api/project'
import { saveModuleDataTracked } from '../api/v2'
import ModuleProgressSidebar from '../components/ModuleProgressSidebar.vue'
import KnowledgePanel from '../components/KnowledgePanel.vue'
import ForeshadowPanel from '../components/ForeshadowPanel.vue'
import ConsistencyPanel from '../components/ConsistencyPanel.vue'
import GenerationStatusBar from '../components/GenerationStatusBar.vue'
import ExportView from './ExportView.vue'
import OnboardingGuide from '../components/OnboardingGuide.vue'
import { useAIGuard } from '../composables/useAIGuard'
import { setupConfirm } from '../composables/useConfirm'
import { setConfirmOverflowHandler } from '../composables/useConfirm'
import { useToastStore } from '../stores/toast'
import TemplateSelector from '../components/TemplateSelector.vue'
import SaveAsTemplate from '../components/SaveAsTemplate.vue'
import IdeaView from './IdeaView.vue'
import ProjectView from './ProjectView.vue'
import WorldView from './WorldView.vue'
import CharacterView from './CharacterView.vue'
import StoryArchitectureView from './StoryArchitectureView.vue'
import PowerSystemView from './PowerSystemView.vue'
import FactionsView from './FactionsView.vue'
import PlanningView from './PlanningView.vue'
import SceneDesignView from './SceneDesignView.vue'
import DraftInlineView from './DraftInlineView.vue'
import ContentView from './ContentView.vue'
import TimelineView from './TimelineView.vue'
import OutlineView from './OutlineView.vue'
import { useTemplateStore } from '../composables/useTemplateStore'
import type { GenerationTemplate } from '../composables/useTemplateStore'

const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const projectStore = useProjectStore()
const moduleSaveStore = useModuleSaveStore()
const toast = useToastStore()
const confirmDialog = setupConfirm()
const projectNameError = ref('')

function reloadPage() { window.location.reload() }

function validateProjectName() {
  const name = projectName.value.trim()
  if (!name) { projectNameError.value = '项目名称不能为空'; return }
  if (name.length < 2) { projectNameError.value = '名称至少2个字符'; return }
  if (/[<>\\\/]/.test(name)) { projectNameError.value = '名称包含无效字符'; return }
  projectNameError.value = ''
}
setConfirmOverflowHandler((opts) => {
  toast.warning('操作队列已满，请完成当前确认后再继续')
})

const _isNewProject = route.query.new === '1'
const projectId = ref(route.query.projectId as string || (_isNewProject ? generateId() : generateId()))
const projectName = ref(_isNewProject ? (route.query.name as string || '新项目') : (route.query.projectId ? '' : '我的小说V2'))
const modules = ref<any[]>([])
const existingProjects = ref<any[]>([])
const restoreNotice = ref('')
const moduleSavedMap = ref<Record<string, boolean>>({})
const showAIGuard = ref(false)
const showOnboarding = ref(false)
const modulesLoadError = ref('')
const pageLoading = ref(true)
const saving = ref(false)
const completing = ref(false)
const { isAIConfigured } = useAIGuard()

const currentModule = computed(() => {
  const m = route.params.module as string
  return m || pipeline.currentModule || 'idea'
})

const currentModuleInfo = computed(() => {
  return modules.value.find(m => m.name === currentModule.value)
})

const progressPct = computed(() => pipeline.progressPct)

const currentModuleIndex = computed(() => {
  return modules.value.findIndex(m => m.name === currentModule.value)
})

const canGoPrev = computed(() => currentModuleIndex.value > 0)
const canGoNext = computed(() => currentModuleIndex.value < modules.value.length - 1)

const hasModuleData = computed(() => {
  const data = pendingModuleData.value[currentModule.value]
  return data !== undefined && data !== null
})

const moduleDependencyStates = computed((): Record<string, 'locked' | 'ready' | 'done'> => {
  const states: Record<string, 'locked' | 'ready' | 'done'> = {}
  const progressModules = pipeline.progress?.modules || {}
  for (const mod of modules.value) {
    const status = progressModules[mod.name]?.status
    if (status === 'done') {
      states[mod.name] = 'done'
    } else if (status === 'locked') {
      states[mod.name] = 'locked'
    } else {
      states[mod.name] = 'ready'
    }
  }
  return states
})



const allModulesData = ref<Record<string, any>>({})
const sidebarStats = computed(() => {
  const d = allModulesData.value
  const vols = d['volumes']
  const cps = d['chapter_plan']
  const drafts = d['draft_generation']
  const chars = d['characters']
  const charList = Array.isArray(chars) ? chars : []
  const charCount = charList.length

  let totalWords = 0
  if (Array.isArray(drafts)) {
    drafts.forEach((dr: any) => {
      const c = dr.content || dr.content_raw || ''
      totalWords += c.length
    })
  } else if (cps) {
    const cpArr = Array.isArray(cps) ? cps : []
    cpArr.forEach((cp: any) => { totalWords += cp.target_words || 0 })
  }

  return {
    volumes: Array.isArray(vols) ? vols.length : 0,
    chapters: Array.isArray(cps) ? cps.length : (Array.isArray(drafts) ? drafts.length : 0),
    words: totalWords > 10000 ? (totalWords / 10000).toFixed(1) + 'w' : totalWords.toString(),
    characters: charCount,
  }
})

function hasUnsavedChanges(): boolean {
   return moduleSaveStore.hasUnsavedChanges(projectId.value) ||
          (!!pendingModuleData.value[currentModule.value] &&
           !moduleSavedMap.value[currentModule.value])
  }

  function isSavingModule(): boolean {
    return moduleSaveStore.isModuleSaving(projectId.value, currentModule.value)
  }

  async function saveCurrentModule(): Promise<boolean> {
    const moduleKey = currentModule.value
    const pending = pendingModuleData.value[moduleKey]
    if (!pending) {
      toast.info('当前模块没有需要保存的数据')
      return false
    }
    moduleSaveStore.markSaving(projectId.value, moduleKey)
    try {
      await saveModuleData(projectId.value, moduleKey, pending)
      moduleSavedMap.value[moduleKey] = true
      moduleSaveStore.markSaved(projectId.value, moduleKey)
      toast.success(`模块"${currentModuleInfo.value?.display_name || moduleKey}"已保存`)
      return true
    } catch (e: any) {
      moduleSaveStore.markError(projectId.value, moduleKey, e?.message || '保存失败')
      toast.error(`模块"${currentModuleInfo.value?.display_name || moduleKey}"保存失败: ${e?.message || ''}`)
      return false
    }
  }

  async function goToProjects() {
    if (hasUnsavedChanges()) {
      const ok = await confirmDialog.confirm({
        title: '未保存的更改',
        message: `有 ${moduleSaveStore.getGlobalUnsavedCount()} 个模块未保存，离开将丢失数据。`,
        confirmText: '离开',
        cancelText: '取消',
        type: 'warning',
      })
      if (!ok) return
    }
    router.push('/projects')
  }

  async function goToTemplates() {
    if (hasUnsavedChanges()) {
      const ok = await confirmDialog.confirm({
        title: '未保存的更改',
        message: `有 ${moduleSaveStore.getGlobalUnsavedCount()} 个模块未保存，离开将丢失数据。`,
        confirmText: '离开',
        cancelText: '取消',
        type: 'warning',
      })
      if (!ok) return
    }
    router.push('/templates')
  }

  async function handleNewProject() {
    if (hasUnsavedChanges()) {
      const ok = await confirmDialog.confirm({
        title: '未保存的更改',
        message: `当前项目有未保存的数据，新建项目将丢失这些数据。`,
        confirmText: '新建',
        cancelText: '取消',
        type: 'warning',
      })
      if (!ok) return
    }
    router.push({ path: '/create-v2', query: { new: '1' } })
  }

async function goToModule(moduleName: string) {
   if (hasUnsavedChanges()) {
     const ok = await confirmDialog.confirm({
       title: '未保存的更改',
       message: '当前模块有未保存的数据，确定要离开吗？',
       confirmText: '离开',
       cancelText: '取消',
       type: 'warning',
     })
     if (!ok) return
   }
   await flushAllSaves()
   router.push({ path: `/create-v2/${moduleName}`, query: { projectId: projectId.value } })
 }

function openSettings() {
  document.querySelector('.settings-btn')?.dispatchEvent(new Event('click'))
}

async function prevModule() {
   if (canGoPrev.value) {
     await flushAllSaves()
     await goToModule(modules.value[currentModuleIndex.value - 1].name)
   }
}

async function nextModule() {
   if (canGoNext.value) {
     await flushAllSaves()
     await goToModule(modules.value[currentModuleIndex.value + 1].name)
   }
}

async function completeAndNext() {
    if (completing.value) return
    if (!hasModuleData.value) {
      toast.warning('当前模块没有数据，请先完成输入输出后再继续')
      return
    }
    if (canGoNext.value) {
       completing.value = true
       try {
         const pending = pendingModuleData.value[currentModule.value]
         try {
           await saveModuleData(projectId.value, currentModule.value, pending)
           moduleSavedMap.value[currentModule.value] = true
         } catch (_e) {
           toast.error('保存模块数据失败，请重试')
           return
         }
         pipeline.updateModuleStatus(currentModule.value, 'done')
         try {
           await updateModuleStatus(projectId.value, currentModule.value, 'done')
         } catch (_e) {
           console.warn('[CreateV2] backend status sync failed:', _e)
         }
         await flushAllSaves()
         nextModule()
       } finally {
         completing.value = false
       }
   }
  }

 // P2-1: Skip a non-critical module
 async function skipModule() {
   if (nonSkippableModules.includes(currentModule.value)) {
     toast.warning('当前模块为关键模块，不能跳过')
     return
   }
   if (canGoNext.value) {
     pipeline.updateModuleStatus(currentModule.value, 'skipped')
     nextModule()
   }
 }

const pendingModuleData = ref<Record<string, any>>({})

async function onModuleComplete(moduleData?: any) {
  if (moduleData) {
    pendingModuleData.value[currentModule.value] = moduleData
    try {
      await saveModuleData(projectId.value, currentModule.value, moduleData)
      moduleSavedMap.value[currentModule.value] = true
    } catch (_e) {
      console.error('[CreateV2] save module data failed:', _e)
      toast.error('保存模块数据失败')
      return
    }

    // Update shared context for template matching
    tplStore.updateSharedContext(currentModule.value, moduleData, projectId.value)

    // Extract project-level context from idea/project module
    if (currentModule.value === 'idea') {
      const genre = moduleData.genre || moduleData.genreHint || ''
      const audience = moduleData.target_audience || ''
      if (genre) currentProjectGenre.value = genre
      if (audience) currentProjectAudience.value = audience
    }
    if (currentModule.value === 'project') {
      const subGenre = moduleData.sub_genre || moduleData.subGenre || ''
      const tone = moduleData.tone || moduleData.style || ''
      if (subGenre) currentProjectSubGenre.value = subGenre
      if (tone) currentProjectTone.value = tone
    }
    if (currentModule.value === 'world') {
      const worldType = moduleData.world_type || moduleData.worldType ||
        moduleData.world_building?.world_type || moduleData.world_building?.worldType || ''
      if (worldType) {
        tplStore.updateSharedContext('world', { world_type: worldType }, projectId.value)
      }
    }

    // Show save-as-template prompt for template-supported modules
    if (templateSupportedModules.includes(currentModule.value)) {
      const inputCtx = {
        genre: currentProjectGenre.value,
        sub_genre: currentProjectSubGenre.value,
        tone: currentProjectTone.value,
        world_type: (tplStore.sharedContext as any).worldType,
        target_audience: currentProjectAudience.value,
      }
      toast.action(`模块"${currentModuleInfo.value?.display_name || currentModule.value}"已完成`, {
        label: '存为模板',
        handler: () => openSaveAsTemplate(moduleData, inputCtx),
      })
    }
  }
  try {
    pipeline.updateModuleStatus(currentModule.value, 'done')
    updateModuleStatus(projectId.value, currentModule.value, 'done').catch((_: any) => {
      console.warn('[CreateV2] backend status sync failed:', _)
    })
  } catch (e: any) {
    toast.error('更新模块状态失败，数据已保存但进度未同步')
    console.error('[CreateV2] update module status failed:', e)
  }
  nextModule()
}

const saveSuccess = ref(false)
let saveSuccessTimer: ReturnType<typeof setTimeout> | null = null
const showExport = ref(false)

// Project-level context for template matching
const currentProjectGenre = ref('')
const currentProjectSubGenre = ref('')
const currentProjectTone = ref('')
const currentProjectAudience = ref('')

// === 模板系统 ===
const { isOnline } = useNetworkStatus()
const tplStore = useTemplateStore()
const showTemplateSelector = ref(false)
const showSaveAsTemplate = ref(false)
const currentTemplateData = ref<any>(null)
const currentTemplateInputCtx = ref<Record<string, any>>({})
const selectedTemplateModules = ref<Record<string, string>>({})

// Available modules that support template
const templateSupportedModules = [
  'world', 'characters', 'factions', 'power_system',
  'story_architecture', 'outline', 'volumes', 'chapter_plan',
  'chapter_outline', 'scene_design', 'plot_nodes'
]

// P2-1: Key modules that cannot be skipped (core design layer)
const nonSkippableModules = ['idea', 'project', 'story_architecture', 'outline']

const projectContextForTemplate = computed(() => ({
  genre: currentProjectGenre.value || '',
  world_type: (tplStore.sharedContext as any).worldType || '',
  sub_genre: currentProjectSubGenre.value || '',
  tone: currentProjectTone.value || '',
  target_audience: currentProjectAudience.value || '',
}))

function openTemplateSelector() {
  if (!templateSupportedModules.includes(currentModule.value)) {
    toast.info('该模块暂不支持模板选择')
    return
  }
  showTemplateSelector.value = true
}

function handleTemplateSelectAI() {
  showTemplateSelector.value = false
  // User chose AI generation, just close and let them use the normal flow
}

function handleTemplateApply(data: any, template: GenerationTemplate) {
  showTemplateSelector.value = false
  selectedTemplateModules.value[currentModule.value] = String(template.id)
  // Save the template data to the project
  pendingModuleData.value[currentModule.value] = data
  saveModuleData(projectId.value, currentModule.value, data).then(() => {
    moduleSavedMap.value[currentModule.value] = true
    toast.success(`已应用模板: ${template.name}`)
    // Update shared context
    tplStore.updateSharedContext(currentModule.value, data, projectId.value)
    // Offer to save as template (the applied data is already a template, so skip)
    nextModule()
  }).catch((e: any) => {
    toast.error('应用模板失败: ' + (e.message || ''))
  })
}

function openSaveAsTemplate(data: any, inputCtx: Record<string, any>) {
  currentTemplateData.value = data
  currentTemplateInputCtx.value = inputCtx
  showSaveAsTemplate.value = true
}

function handleTemplateSaved(template: GenerationTemplate) {
  toast.success(`模板"${template.name}"已保存`)
  showSaveAsTemplate.value = false
}

// Provide template functions to child views
provide('templateSystem', {
  openTemplateSelector,
  openSaveAsTemplate,
  isTemplateSupported: (moduleKey: string) => templateSupportedModules.includes(moduleKey),
  currentModuleKey: currentModule,
  projectId,
})

function formatProjectDate(d: string): string {
  if (!d) return '-'
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  return dt.toISOString().replace('T', ' ').slice(0, 19)
}

function flashSaveSuccess() {
  saveSuccess.value = true
  if (saveSuccessTimer) clearTimeout(saveSuccessTimer)
  saveSuccessTimer = setTimeout(() => { saveSuccess.value = false }, 2000)
}

async function saveProject() {
   pendingModuleData.value['__progress'] = pipeline.progress
   await projectStore.saveV2Full({
     id: projectId.value,
     name: projectName.value,
     pipeline: { ...pipeline.progress, moduleData: pendingModuleData.value },
   })
   flashSaveSuccess()
}

/**
 * 全量保存V2项目：收集所有模块数据(包括DB中的) + 流水线状态
 */
async function saveProjectFull() {
   if (!projectId.value) {
     toast.error('项目ID无效')
     return
   }
   saving.value = true
   try {
     // 1. 从后端获取所有模块的完整数据
     const allData = await getAllModuleData(projectId.value)
     const modules = allData?.modules || {}

     // 2. 合并前端pending数据(前端数据更新)
     for (const [k, v] of Object.entries(pendingModuleData.value)) {
       if (k !== '__progress' && v != null) {
         modules[k] = v
       }
     }

     // 3. 构造流水线状态
     const pipelineState = {
       currentModule: currentModule.value,
       modules: {} as Record<string, any>,
     }
      const allMods = modules.value
      for (const mod of allMods) {
        const name = mod.name
        const modState: any = pipeline.progress?.modules?.[name] || {}
        pipelineState.modules[name] = {
          status: modules[name] ? (modState.status === 'done' ? 'done' : 'done') : (modState.status || 'pending'),
          completedAt: modState.completedAt || '',
        }
      }

     // 4. 保存
     const result = await projectStore.saveV2Full({
       id: projectId.value,
       name: projectName.value || '未命名项目',
       modules,
       pipeline: pipelineState,
       templateSelections: selectedTemplateModules.value,
       sharedContext: tplStore.sharedContext || {},
     })

     // 归档哪些模块失败了
     if (result.failedModules?.length) {
       toast.warning(`部分模块保存失败: ${result.failedModules.join(', ')}`)
       for (const fm of result.failedModules) {
         moduleSaveStore.markError(projectId.value, fm, '全量保存失败')
       }
     } else {
       toast.success(`项目已保存 (${Object.keys(modules).length} 个模块)`)
       // 标记所有模块已保存
       for (const k of Object.keys(modules)) {
         moduleSaveStore.markSaved(projectId.value, k)
         moduleSavedMap.value[k] = true
       }
     }

      flashSaveSuccess()
    } catch (e: any) {
      if (e.status === 409) {
        toast.error('项目已被其他标签页修改，请刷新后重试')
      } else {
        toast.error('保存失败: ' + (e.message || ''))
      }
    } finally {
      saving.value = false
    }
  }

function startNewProject() {
   handleNewProject()
  }

   async function switchProject() {
     if (!projectId.value) return
     if (hasUnsavedChanges()) {
       const ok = await confirmDialog.confirm({
         title: '未保存的更改',
         message: '当前模块有未保存的数据，切换项目将丢失这些数据，确定要继续吗？',
         confirmText: '保存并切换',
         cancelText: '取消',
         type: 'warning',
       })
       if (!ok) return
       try {
         await flushAllSaves()
       } catch (_e) { /* continue even if save fails */ }
     }
     moduleSaveStore.clearProject(projectId.value)
     await pipeline.loadStatus(projectId.value)
     tplStore.activateProject(projectId.value)
     modules.value = pipeline.modules
     restoreNotice.value = ''
     selectedTemplateModules.value = {}
     currentProjectGenre.value = ''
     currentProjectSubGenre.value = ''
     currentProjectTone.value = ''
     currentProjectAudience.value = ''
     // 恢复项目名
     try {
       const v2Data = await loadV2Project(projectId.value)
       if (v2Data?.name) {
         projectName.value = v2Data.name
       }
     } catch (_e) { /* ignore */ }
     router.push({ path: '/create-v2', query: { projectId: projectId.value } })
   }

  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (hasUnsavedChanges()) {
      e.preventDefault()
      e.returnValue = ''
    }
  }

  onMounted(async () => {
   pageLoading.value = true
   try {
     await pipeline.loadModules()
   } catch (e: any) {
     modulesLoadError.value = e?.message || '加载模块列表失败'
     pageLoading.value = false
     return
   }
   modules.value = pipeline.modules
   // 5.1-1: Auto-project-state when entering without a project
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
      // 确保项目列表已加载
      if (!projectStore.projectList || projectStore.projectList.length === 0) {
        await projectStore.loadList()
      }
      existingProjects.value = projectStore.projectList || []
    } catch (_e) {
      console.error('[CreateV2] preload existing projects failed:', _e)
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
      // Restore project context for template matching
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
      const facData = v2Data?.modules?.['factions']
     if (facData) tplStore.updateSharedContext('factions', facData, projectId.value)
  } catch (_e) {
    console.error('[CreateV2] restore module data failed:', _e)
  }

  const hasSeenOnboarding = localStorage.getItem('onboarding_seen_v2')
  const hasExistingProgress = Object.values(pipeline.progress?.modules || {}).some((m: any) => m.status === 'done')
  if (!hasSeenOnboarding && !hasExistingProgress) {
    showOnboarding.value = true
    localStorage.setItem('onboarding_seen_v2', '1')
  }

  // P3-4: prompt for name when entering create-v2 directly without a project name
  if (_isNewProject && !route.query.name && projectName.value === '新项目') {
    const name = window.prompt('请输入项目名称：', '')
    if (name && name.trim()) {
      projectName.value = name.trim().slice(0, 64)
    }
  }

  window.addEventListener('beforeunload', handleBeforeUnload)

  // Handle applyTemplate from TemplateLibrary
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
      console.error('[CreateV2] applyTemplate failed:', _e)
      toast.error('应用模板失败')
    }
  }

  pageLoading.value = false
})

/**
 * 加载指定项目的数据 — 从路由query.projectId读取，恢复流水线状态和项目名
 */
async function loadProjectFromRoute() {
  const pid = route.query.projectId as string
  if (!pid) return
  projectId.value = pid
  pageLoading.value = true
  try {
    await pipeline.loadStatus(pid)
    tplStore.activateProject(pid)
    // 用 loadV2Project 获取项目名+模块数据
    const v2Data = await loadV2Project(pid)
    projectName.value = v2Data?.name || projectName.value || '未命名项目'
    allModulesData.value = v2Data?.modules || {}
    // 恢复模板上下文
    const ideaData = v2Data?.modules?.['idea']
    if (ideaData) {
      currentProjectGenre.value = ideaData.genre || ideaData.genreHint || ''
      currentProjectAudience.value = ideaData.target_audience || ''
    }
    const worldData = v2Data?.modules?.['world']
    if (worldData) {
      const wbData = worldData.world_building || worldData
      tplStore.updateSharedContext('world', {
        world_type: wbData.world_type || wbData.worldType || '',
        locations: wbData.locations || wbData.territories || [],
      }, pid)
    }
  } catch (e) {
    console.error('[CreateV2] loadProjectFromRoute failed:', e)
  } finally {
    pageLoading.value = false
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (saveSuccessTimer) clearTimeout(saveSuccessTimer)
})

watch(() => route.params.module, async (newModule) => {
  if (newModule) {
    await pipeline.loadStatus(projectId.value)
  }
})

// 监听路由projectId变化 — 处理项目切换后模块跳转的场景
watch(() => route.query.projectId, async (newPid) => {
  if (newPid && newPid !== projectId.value) {
    await loadProjectFromRoute()
  }
})

watch(isAIConfigured, (val) => {
  showAIGuard.value = !val
}, { immediate: true })

let _loadRequestId = 0
watch(projectId, async (newPid) => {
  if (newPid) {
    const requestId = ++_loadRequestId
    try {
      const v2Data = await loadV2Project(newPid)
      if (requestId === _loadRequestId) {
        allModulesData.value = v2Data?.modules || {}
        if (v2Data?.name) projectName.value = v2Data.name
      }
    } catch (_e) {
      console.error('[CreateV2] load module data failed:', _e)
    }
  }
})
</script>

<style scoped>
.create-v2 {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
  overflow: hidden;
}
.v2-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 23px 28px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.v2-header h2 { font-size: 26px; margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.project-select { padding: 10px 14px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; max-width: 280px; cursor: pointer; }
.project-name-input {
   padding: 10px 14px;
   border: 1px solid #ddd;
   border-radius: 10px;
   font-size: 16px;
}
.project-name-error {
  color: #ff4d4f;
  font-size: 12px;
  white-space: nowrap;
}
.btn-save { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; position: relative; }
.btn-help { padding: 10px 16px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 10px; cursor: pointer; font-size: 15px; }
.save-toast { color: #fff; font-weight: 600; }
.restore-notice { background: #f6ffed; border-bottom: 1px solid #b7eb8f; padding: 8px 28px; color: #52c41a; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }
.btn-dismiss { background: none; border: none; font-size: 18px; color: #52c41a; cursor: pointer; padding: 0 8px; }
.v2-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.v2-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.module-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 28px;
  background: #f9f9f9;
  border-bottom: 1px solid #eee;
}
.btn-nav { padding: 10px 18px; background: #fff; border: 1px solid #ddd; border-radius: 10px; cursor: pointer; font-size: 15px; }
.btn-nav:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-next { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn-skip { background: #f0f0f0; color: #999; }
.btn-skip:hover:not(:disabled) { background: #e0e0e0; color: #666; }
.module-title { font-weight: 600; font-size: 20px; color: var(--primary); display: flex; align-items: center; gap: 8px; }
.save-badge { font-size: 12px; background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 4px; }
.module-content { flex: 1; overflow-y: auto; padding: 28px 36px; }
.module-placeholder { text-align: center; padding: 80px 28px; color: #888; font-size: 18px; }
.btn-skip { margin-top: 26px; padding: 16px 28px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 10px; cursor: pointer; font-size: 21px; }
.v2-side-panel {
  width: 468px;
  background: #fafafa;
  border-left: 1px solid #eee;
  overflow-y: auto;
  padding: 21px;
}
.btn-export { padding: 10px 20px; background: #f0f0f0; color: #555; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; }
.btn-export:hover { background: #e0e0e0; }
.btn-projects { display: flex; align-items: center; padding: 10px 16px; background: #f0f0f0; color: #555; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; text-decoration: none; }
.btn-projects:hover { background: #e0e0e0; }
.btn-new-project { padding: 10px 16px; background: #52c41a; color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; font-weight: 600; }
.btn-new-project:hover { background: #73d13d; }
.export-panel { margin: 20px 0; }
.ai-guard-banner {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  padding: 10px 20px; background: #fff7e6; border: 1px solid #ffd591;
  border-radius: 8px; margin-bottom: 12px; font-size: 14px; color: #d46b08;
}
.btn-config-ai { padding: 4px 14px; background: #fa8c16; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-config-ai:hover { background: #ff9c6e; }
.btn-template {
  padding: 10px 16px;
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn-template:hover {
  background: #d9f7be;
  border-color: #73d13d;
}
.offline-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 20px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #d46b08;
}
.error-page { text-align: center; padding: 80px 28px; color: #e74c3c; }
.error-page h3 { font-size: 22px; margin-bottom: 12px; }
.error-page p { font-size: 15px; margin-bottom: 20px; color: #888; }
.page-loading-full { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; gap: 16px; color: #666; font-size: 16px; }
.btn-spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 4px; }
.btn-save-module { padding: 10px 16px; background: #52c41a; color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; }
.btn-save-module:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-save-module:hover:not(:disabled) { background: #73d13d; }
</style>
