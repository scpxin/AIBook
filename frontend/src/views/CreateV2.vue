<template>
  <div class="create-v2">
    <GenerationStatusBar />
    <div class="v2-header">
      <h2>AI创作V2 — 19模块流水线</h2>
      <div class="header-actions">
        <select v-model="projectId" @change="switchProject" class="project-select">
          <option :value="projectId">{{ projectName || '当前项目' }}</option>
          <option v-for="p in existingProjects" :key="p.id" :value="p.id">
            {{ p.name }}（{{ p.updated_at }}）
          </option>
        </select>
        <input v-model="projectName" placeholder="项目名称" class="project-name-input" />
        <button @click="saveProject" class="btn-save">
          <span v-if="saveSuccess" class="save-toast">已保存!</span>
          <span v-else>保存项目</span>
        </button>
        <button @click="showExport = !showExport" class="btn-export">导出</button>
      </div>
    </div>

    <div v-if="showExport" class="export-panel">
      <ExportView :project-id="projectId" />
    </div>

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
        @select="goToModule"
      />

      <div class="v2-main">
        <div class="module-nav">
          <button @click="prevModule" :disabled="!canGoPrev" class="btn-nav">← 上一步</button>
          <span class="module-title">
            {{ currentModuleInfo?.display_name || currentModule }}
            <span v-if="moduleSavedMap[currentModule]" class="save-badge">已保存</span>
          </span>
          <button @click="completeAndNext" :disabled="!canGoNext" class="btn-nav btn-next">下一步 →</button>
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
            <PowerSystemView v-else-if="currentModule === 'power_system'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
            <FactionsView v-else-if="currentModule === 'factions'" :key="currentModule + projectId" :project-id="projectId" @complete="onModuleComplete" />
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePipelineStore } from '../stores/pipeline'
import { useProjectStore } from '../stores/project'
import { generateId } from '../utils'
import { saveModuleData, getAllModuleData } from '../api/v2'
import ModuleProgressSidebar from '../components/ModuleProgressSidebar.vue'
import KnowledgePanel from '../components/KnowledgePanel.vue'
import ForeshadowPanel from '../components/ForeshadowPanel.vue'
import ConsistencyPanel from '../components/ConsistencyPanel.vue'
import GenerationStatusBar from '../components/GenerationStatusBar.vue'
import ExportView from './ExportView.vue'
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

const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const projectStore = useProjectStore()

const projectId = ref(route.query.projectId as string || generateId())
const projectName = ref('我的小说V2')
const modules = ref<any[]>([])
const existingProjects = ref<any[]>([])
const restoreNotice = ref('')
const moduleSavedMap = ref<Record<string, boolean>>({})

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

async function goToModule(moduleName: string) {
  autoSaveCurrentModule()
  await saveCurrentModuleData()
  router.push({ path: `/create-v2/${moduleName}`, query: { projectId: projectId.value } })
}

async function saveCurrentModuleData() {
  // Trigger auto-save event for child components that registered listeners
  const event = new CustomEvent('module-auto-save', { detail: { module: currentModule.value, projectId: projectId.value } })
  window.dispatchEvent(event)
  // Small delay to let async save operations start
  await new Promise(r => setTimeout(r, 100))
}

function prevModule() {
  if (canGoPrev.value) {
    goToModule(modules.value[currentModuleIndex.value - 1].name)
  }
}

function nextModule() {
  if (canGoNext.value) {
    goToModule(modules.value[currentModuleIndex.value + 1].name)
  }
}

function completeAndNext() {
  if (canGoNext.value) {
    pipeline.updateModuleStatus(currentModule.value, 'done')
    nextModule()
  }
}

const pendingModuleData = ref<Record<string, any>>({})

async function onModuleComplete(moduleData?: any) {
  pipeline.updateModuleStatus(currentModule.value, 'done')
  if (moduleData) {
    pendingModuleData.value[currentModule.value] = moduleData
    try {
      await saveModuleData(projectId.value, currentModule.value, moduleData)
      moduleSavedMap.value[currentModule.value] = true
    } catch (_e) { /* ignore */ }
  }
  nextModule()
}

const saveSuccess = ref(false)
const showExport = ref(false)

async function saveProject() {
  pendingModuleData.value['__progress'] = pipeline.progress
  await projectStore.saveV2({
    id: projectId.value,
    name: projectName.value,
    pipelineData: { ...pipeline.progress, moduleData: pendingModuleData.value },
  })
  saveSuccess.value = true
  setTimeout(() => { saveSuccess.value = false }, 2000)
}

function autoSaveCurrentModule() {
  // Hook for child components to register auto-save via event bus pattern
  const event = new CustomEvent('module-auto-save', { detail: { module: currentModule.value, projectId: projectId.value } })
  window.dispatchEvent(event)
}

async function switchProject() {
  if (!projectId.value) return
  await pipeline.loadStatus(projectId.value)
  modules.value = pipeline.modules
  restoreNotice.value = ''
  router.push({ path: '/create-v2', query: { projectId: projectId.value } })
}

onMounted(async () => {
  await pipeline.loadModules()
  modules.value = pipeline.modules
  await pipeline.loadStatus(projectId.value)

  const doneCount = Object.values(pipeline.progress?.modules || {}).filter((m: any) => m.status === 'done').length
  if (doneCount > 0) {
    restoreNotice.value = `已从上次进度恢复：已完成 ${doneCount} / ${modules.value.length} 个模块（当前：${pipeline.currentModule}）`
  }

  try {
    existingProjects.value = projectStore.projectList || []
  } catch (_e) { /* ignore */ }

  try {
    const allData = await getAllModuleData(projectId.value)
    allModulesData.value = allData?.modules || {}
  } catch (_e) { /* ignore */ }
})

watch(() => route.params.module, async (newModule) => {
  if (newModule) {
    await pipeline.loadStatus(projectId.value)
  }
})

watch(projectId, async (newPid) => {
  if (newPid) {
    try {
      const allData = await getAllModuleData(newPid)
      allModulesData.value = allData?.modules || {}
    } catch (_e) { /* ignore */ }
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
.btn-save { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 15px; position: relative; }
.save-toast { color: #fff; font-weight: 600; }
.restore-notice { background: #f6ffed; border-bottom: 1px solid #b7eb8f; padding: 8px 28px; color: #52c41a; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }
.btn-dismiss { background: none; border: none; font-size: 18px; color: #52c41a; cursor: pointer; padding: 0 8px; }
.v2-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
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
.export-panel { margin: 20px 0; }
</style>
