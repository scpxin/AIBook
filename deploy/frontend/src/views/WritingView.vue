<template>
  <div class="writing-view">
    <div class="writing-layout">
      <div class="chapter-selector">
        <h4>章节选择</h4>
        <div v-for="(ch, idx) in chapters" :key="idx" class="chapter-item" :class="{ active: currentChapterIdx === idx }" @click="selectChapter(idx)">
          <span class="ch-num">第{{ idx + 1 }}章</span>
          <span class="ch-title">{{ ch.title }}</span>
          <span v-if="ch.wordCount" class="ch-progress">{{ ch.wordCount }}字</span>
        </div>
      </div>

      <div class="writing-main">
        <div class="outline-section" v-if="currentOutline">
          <h4>{{ currentOutline.title }} — 章节细纲</h4>
          <div v-for="(s, si) in currentOutline.scenes" :key="si" class="scene-outline">
            <span class="scene-label">场景{{ si + 1 }}:</span>
            <span class="scene-text">{{ s }}</span>
          </div>
        </div>

        <StreamingOutput
          :content="draftContent"
          :streaming="isGenerating"
          placeholder="点击下方按钮开始生成正文..."
        />

        <div class="writing-toolbar">
          <button @click="generateDraft" :disabled="isGenerating" class="btn-generate">
            {{ isGenerating ? '生成中...' : '生成正文' }}
          </button>
          <button @click="polish" :disabled="isGenerating || !draftContent" class="btn-tool">润色</button>
          <button @click="rewrite" :disabled="isGenerating || !draftContent" class="btn-tool">重写</button>
          <button @click="parse" :disabled="isGenerating || !draftContent" class="btn-tool">解析</button>
          <button @click="save" :disabled="!draftContent" class="btn-save">保存</button>
        </div>
      </div>

      <div class="writing-side">
        <KnowledgePanel :project-id="projectId" />
        <ForeshadowPanel :project-id="projectId" />
        <ConsistencyPanel :project-id="projectId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExecutionStore } from '../stores/execution'
import StreamingOutput from '../components/StreamingOutput.vue'
import KnowledgePanel from '../components/KnowledgePanel.vue'
import ForeshadowPanel from '../components/ForeshadowPanel.vue'
import ConsistencyPanel from '../components/ConsistencyPanel.vue'
import * as v2Api from '../api/v2'

const route = useRoute()
const execution = useExecutionStore()

const projectId = ref(route.query.projectId as string || '')
const chapters = ref<any[]>([])
const currentChapterIdx = ref(0)
const draftContent = ref('')
const isGenerating = ref(false)

const currentOutline = computed(() => {
  if (!chapters.value.length) return null
  return chapters.value[currentChapterIdx.value]?.outline || null
})

function selectChapter(idx: number) {
  currentChapterIdx.value = idx
  draftContent.value = chapters.value[idx].content || ''
}

async function generateDraft() {
  isGenerating.value = true
  draftContent.value = ''
  try {
    const chapter = chapters.value[currentChapterIdx.value]
    await execution.generateDraft(projectId.value, chapter.id, (text: string) => {
      draftContent.value += text
    })
  } finally {
    isGenerating.value = false
  }
}

async function polish() {
  isGenerating.value = true
  try {
    const result = await execution.polishDraft(projectId.value, draftContent.value)
    draftContent.value = result.content
  } finally {
    isGenerating.value = false
  }
}

async function rewrite() {
  isGenerating.value = true
  draftContent.value = ''
  try {
    const chapter = chapters.value[currentChapterIdx.value]
    await execution.generateDraft(projectId.value, chapter.id, (text: string) => {
      draftContent.value += text
    })
  } finally {
    isGenerating.value = false
  }
}

async function parse() {
  const result = await execution.parseContent(projectId.value, draftContent.value)
  // Show parse result in some way
}

async function save() {
  const chapter = chapters.value[currentChapterIdx.value]
  await v2Api.saveDraft(projectId.value, chapter.id, draftContent.value)
}

onMounted(async () => {
  if (projectId.value) {
    const chaptersData = await execution.getChaptersForWriting(projectId.value)
    chapters.value = chaptersData
  }
})
</script>

<style scoped>
.writing-view { height: 100%; }
.writing-layout { display: flex; height: 100%; gap: 0; }
.chapter-selector {
  width: 180px;
  background: #fafafa;
  border-right: 1px solid #eee;
  overflow-y: auto;
  padding: 12px 0;
}
.chapter-selector h4 { padding: 0 12px; margin: 0 0 8px; font-size: 13px; }
.chapter-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: 0.15s;
}
.chapter-item:hover { background: #f0f0f0; }
.chapter-item.active { background: #e8f4fd; border-left-color: var(--primary); }
.ch-num { font-size: 12px; color: #888; }
.ch-title { font-size: 13px; font-weight: 500; }
.ch-progress { font-size: 11px; color: #bbb; }
.writing-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.outline-section { padding: 14px 20px; background: #f9f9f9; border-bottom: 1px solid #eee; max-height: 180px; overflow-y: auto; }
.outline-section h4 { margin: 0 0 8px; font-size: 14px; }
.scene-outline { display: flex; gap: 6px; font-size: 12px; padding: 2px 0; }
.scene-label { color: var(--primary); flex-shrink: 0; font-weight: 500; }
.scene-text { color: #666; }
.writing-toolbar { display: flex; gap: 8px; padding: 10px 20px; border-top: 1px solid #eee; background: #fafafa; }
.btn-generate { padding: 8px 20px; background: var(--primary); color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.btn-generate:disabled { opacity: 0.5; cursor: wait; }
.btn-tool { padding: 8px 14px; background: #fff; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-tool:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-save { padding: 8px 14px; background: #52c41a; color: #fff; border: none; border-radius: 4px; cursor: pointer; margin-left: auto; }
.writing-side { width: 260px; background: #fafafa; border-left: 1px solid #eee; overflow-y: auto; padding: 12px; }
</style>
