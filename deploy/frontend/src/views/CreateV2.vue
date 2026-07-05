<template>
  <div class="create-v2">
    <div class="v2-header">
      <h2>AI创作V2 — 18模块流水线</h2>
      <div class="header-actions">
        <input v-model="projectName" placeholder="项目名称" class="project-name-input" />
        <button @click="saveProject" class="btn-save">保存</button>
      </div>
    </div>

    <div class="v2-layout">
      <ModuleProgressSidebar
        :modules="modules"
        :current-module="currentModule"
        :progress-pct="progressPct"
        @select="goToModule"
      />

      <div class="v2-main">
        <div class="module-nav">
          <button @click="prevModule" :disabled="!canGoPrev" class="btn-nav">← 上一步</button>
          <span class="module-title">{{ currentModuleInfo?.displayName || currentModule }}</span>
          <button @click="nextModule" :disabled="!canGoNext" class="btn-nav">下一步 →</button>
        </div>

        <div class="module-content">
          <IdeaView v-if="currentModule === 'idea'" :project-id="projectId" @complete="onModuleComplete" />
          <ProjectView v-else-if="currentModule === 'project'" :project-id="projectId" @complete="onModuleComplete" />
          <WorldView v-else-if="currentModule === 'world'" :project-id="projectId" @complete="onModuleComplete" />
          <CharacterView v-else-if="currentModule === 'characters'" :project-id="projectId" @complete="onModuleComplete" />
          <StoryView v-else-if="currentModule === 'story'" :project-id="projectId" @complete="onModuleComplete" />
          <PlanningView v-else-if="['volumes', 'plotNodes', 'chapterPlan', 'chapterOutline'].includes(currentModule)" :project-id="projectId" :current-module="currentModule" @complete="onModuleComplete" />
          <div v-else class="module-placeholder">
            <h3>{{ currentModuleInfo?.displayName || currentModule }}</h3>
            <p>该模块视图正在建设中...</p>
            <button @click="onModuleComplete(currentModule)" class="btn-skip">跳过此模块</button>
          </div>
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
import ModuleProgressSidebar from '../components/ModuleProgressSidebar.vue'
import KnowledgePanel from '../components/KnowledgePanel.vue'
import ForeshadowPanel from '../components/ForeshadowPanel.vue'
import ConsistencyPanel from '../components/ConsistencyPanel.vue'
import IdeaView from './IdeaView.vue'
import ProjectView from './ProjectView.vue'
import WorldView from './WorldView.vue'
import CharacterView from './CharacterView.vue'
import StoryView from './StoryView.vue'
import PlanningView from './PlanningView.vue'

const route = useRoute()
const router = useRouter()
const pipeline = usePipelineStore()
const projectStore = useProjectStore()

const projectId = ref(route.query.projectId as string || generateId())
const projectName = ref('我的小说V2')
const modules = ref<any[]>([])

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

function goToModule(moduleName: string) {
  router.push({ path: `/create-v2/${moduleName}`, query: { projectId: projectId.value } })
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

function onModuleComplete(moduleName: string) {
  pipeline.updateModuleStatus(moduleName, 'done')
  nextModule()
}

async function saveProject() {
  await projectStore.saveV2({
    id: projectId.value,
    name: projectName.value,
    pipelineData: pipeline.progress,
  })
}

onMounted(async () => {
  await pipeline.loadModules()
  modules.value = pipeline.modules
  await pipeline.loadStatus(projectId.value)
})

watch(() => route.params.module, async (newModule) => {
  if (newModule) {
    await pipeline.loadStatus(projectId.value)
  }
})
</script>

<style scoped>
.create-v2 {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  overflow: hidden;
}
.v2-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.v2-header h2 { font-size: 18px; margin: 0; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.project-name-input {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}
.btn-save { padding: 6px 16px; background: var(--primary); color: #fff; border: none; border-radius: 4px; cursor: pointer; }
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
  padding: 8px 20px;
  background: #f9f9f9;
  border-bottom: 1px solid #eee;
}
.btn-nav { padding: 6px 12px; background: #fff; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-nav:disabled { opacity: 0.4; cursor: not-allowed; }
.module-title { font-weight: 600; font-size: 16px; color: var(--primary); }
.module-content { flex: 1; overflow-y: auto; padding: 20px; }
.module-placeholder { text-align: center; padding: 60px 20px; color: #888; }
.btn-skip { margin-top: 16px; padding: 8px 20px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
.v2-side-panel {
  width: 280px;
  background: #fafafa;
  border-left: 1px solid #eee;
  overflow-y: auto;
  padding: 12px;
}
</style>
