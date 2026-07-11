<template>
  <div class="writing-view">
    <div class="writing-layout">
      <div class="chapter-selector">
        <h4>章节选择</h4>
        <div v-if="!chapters.length" class="empty-chapters">
          <p>{{ loadError || '暂无章节数据' }}</p>
          <p class="empty-tip">请先在「创作V2」中生成章节规划</p>
        </div>
        <div v-for="(ch, idx) in chapters" :key="idx" class="chapter-item" :class="{ active: currentChapterIdx === idx }" @click="selectChapter(idx)">
          <span class="ch-num">第{{ idx + 1 }}章</span>
          <span class="ch-title">{{ ch.title }}</span>
          <span v-if="ch.wordCount" class="ch-progress">{{ ch.wordCount }}字</span>
        </div>
      </div>

      <div class="writing-main">
        <div class="outline-section" v-if="currentOutline">
          <h4>{{ currentOutline.title }} — 章节细纲</h4>
          <p v-if="currentOutline.summary" class="outline-summary">{{ currentOutline.summary }}</p>
          <div v-for="(s, si) in currentOutline.scenes" :key="si" class="scene-outline">
            <span class="scene-label">场景{{ si + 1 }}:</span>
            <span class="scene-text">{{ typeof s === 'string' ? s : (s.title || s.summary || JSON.stringify(s)) }}</span>
          </div>
          <div v-if="currentOutline.key_points?.length" class="outline-points">
            <span class="points-label">关键点：</span>
            <span v-for="(p, pi) in currentOutline.key_points" :key="pi" class="point-tag">{{ p }}</span>
          </div>
          <div v-if="currentOutline.characters?.length" class="outline-chars">
            <span class="chars-label">出场人物：</span>
            <span v-for="(c, ci) in currentOutline.characters" :key="ci" class="char-tag">{{ c }}</span>
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
const loadError = ref('')

const currentOutline = computed(() => {
  if (!chapters.value.length) return null
  const ch = chapters.value[currentChapterIdx.value]
  if (!ch) return null
  return ch.outline && (ch.outline.scenes?.length || ch.outline.summary || ch.outline.key_points?.length)
    ? ch.outline
    : { title: ch.title, summary: '', scenes: [], key_points: [], characters: [] }
})

function selectChapter(idx: number) {
  if (idx < 0 || idx >= chapters.value.length) return
  currentChapterIdx.value = idx
  draftContent.value = chapters.value[idx]?.content || ''
}

async function generateDraft() {
  isGenerating.value = true
  draftContent.value = ''
  try {
    const chapter = chapters.value[currentChapterIdx.value]
    await execution.generateDraft(projectId.value, chapter.id, (text: string) => {
      draftContent.value += text
    })
  } catch {
    // error already shown by store toast
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
  } catch {
    // error already shown by store toast
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
    try {
      const chaptersData = await execution.getChaptersForWriting(projectId.value)
      chapters.value = chaptersData
    } catch (e: any) {
      loadError.value = e.message || '加载章节失败'
    }
  } else {
    loadError.value = '缺少项目ID参数，请从「创作V2」进入写作'
  }
})
</script>

<style scoped>
.writing-view { height: 100%; }
.writing-layout { display: flex; height: 100%; gap: 0; }
.chapter-selector {
  width: 234px;
  background: #fafafa;
  border-right: 1px solid #eee;
  overflow-y: auto;
  padding: 16px 0;
}
.chapter-selector h4 { padding: 0 12px; margin: 0 0 8px; font-size: 17px; }
.chapter-item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: 0.15s;
}
.chapter-item:hover { background: #f0f0f0; }
.chapter-item.active { background: #e8f4fd; border-left-color: var(--primary); }
.ch-num { font-size: 16px; color: #888; }
.ch-title { font-size: 17px; font-weight: 500; }
.ch-progress { font-size: 14px; color: #bbb; }
.writing-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.outline-section { padding: 18px 20px; background: #f9f9f9; border-bottom: 1px solid #eee; max-height: 234px; overflow-y: auto; }
.outline-section h4 { margin: 0 0 8px; font-size: 18px; }
.scene-outline { display: flex; gap: 8px; font-size: 16px; padding: 3px 0; }
.scene-label { color: var(--primary); flex-shrink: 0; font-weight: 500; }
.scene-text { color: #666; }
.outline-summary { font-size: 15px; color: #555; margin: 6px 0; font-style: italic; }
.outline-points, .outline-chars { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; align-items: center; }
.points-label, .chars-label { font-size: 14px; color: #888; font-weight: 500; }
.point-tag, .char-tag { font-size: 13px; background: #e8f4fd; color: #1890ff; padding: 2px 7px; border-radius: 4px; }
.char-tag { background: #f6ffed; color: #52c41a; }
.writing-toolbar { display: flex; gap: 10px; padding: 13px 20px; border-top: 1px solid #eee; background: #fafafa; }
.btn-generate { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 5px; cursor: pointer; }
.btn-generate:disabled { opacity: 0.5; cursor: wait; }
.btn-tool { padding: 10px 14px; background: #fff; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; font-size: 17px; }
.btn-tool:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-save { padding: 10px 14px; background: #52c41a; color: #fff; border: none; border-radius: 5px; cursor: pointer; margin-left: auto; }
.writing-side { width: 338px; background: #fafafa; border-left: 1px solid #eee; overflow-y: auto; padding: 16px; }
.empty-chapters { padding: 20px 12px; text-align: center; color: #999; font-size: 16px; }
.empty-tip { font-size: 14px; color: #bbb; margin-top: 4px; }
</style>
