<template>
  <div>
    <div class="card">
      <h2>网文技法工具箱</h2>
      <div class="tip" style="margin-bottom:8px">拆文分析 · 去AI味 · 质量评分 · 融入网文写作技法</div>
      <div class="craft-subtabs">
        <div class="craft-subtab" :class="{ active: craftTab === 'detect' }" @click="craftTab = 'detect'">去AI味检测</div>
        <div class="craft-subtab" :class="{ active: craftTab === 'deconstruct' }" @click="craftTab = 'deconstruct'">拆文分析</div>
        <div class="craft-subtab" :class="{ active: craftTab === 'quality' }" @click="craftTab = 'quality'">质量评分</div>
      </div>

      <SourceTabs :tabs="sourceTabs" v-model="craftSource" @change="onSourceTabChange" />

      <div v-show="craftSource === 'paste'">
        <textarea v-model="craftText" class="text-area" :placeholder="placeholderText"></textarea>
      </div>
      <div v-show="craftSource === 'saved'">
        <BookSelector :books="savedBooks" v-model="selectedCraftBook" @select="selectCraftBook" />
        <div v-if="!savedBooks.length" class="empty">暂无已下载书籍</div>
      </div>

      <div class="select-row" style="margin-top:8px">
        <ModelSelect v-model="craftModelIdx" />
        <button v-if="craftTab === 'detect'" class="btn btn-craft" @click="runDetectAI()" :disabled="craftLoading"><span v-if="craftLoading" class="spinner"></span>检测AI味</button>
        <button v-if="craftTab === 'deconstruct'" class="btn btn-craft" @click="runDeconstruct()" :disabled="craftLoading"><span v-if="craftLoading" class="spinner"></span>拆解分析</button>
        <button v-if="craftTab === 'quality'" class="btn btn-craft" @click="runQualityScore()" :disabled="craftLoading"><span v-if="craftLoading" class="spinner"></span>质量评分</button>
      </div>
    </div>

    <!-- Detect AI Result -->
    <div class="card" v-if="detectResult">
      <h2>AI味检测结果</h2>
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
        <div style="text-align:center">
          <div class="score-big" :class="'score-' + scoreClass">{{ detectResult.ai_score }}</div>
          <div style="font-size:10px;color:#888">AI味浓度(0-100)</div>
        </div>
        <div style="flex:1">
          <div style="font-size:12px;color:#555;margin-bottom:4px">{{ detectResult.summary }}</div>
          <div style="font-size:11px;color:#888">{{ detectResult.overall_assessment }}</div>
        </div>
      </div>
      <div v-if="detectResult.issues && detectResult.issues.length" style="margin-bottom:10px">
        <div style="font-size:11px;font-weight:600;margin-bottom:4px">检测到 {{ detectResult.issues.length }} 处问题：</div>
        <div v-for="(iss, i) in detectResult.issues" :key="i" class="issue-item">
          <div style="display:flex;justify-content:space-between">
            <span class="tag" :class="'tag-' + (iss.severity >= 4 ? 'red' : iss.severity >= 3 ? 'orange' : 'blue')">{{ iss.type }}</span>
            <span style="font-size:9px;color:#888">严重度 {{ iss.severity }}/5 | {{ iss.position }}</span>
          </div>
          <div class="issue-excerpt">{{ iss.excerpt }}</div>
        </div>
      </div>
      <div v-if="detectResult.issues && detectResult.issues.length">
        <button class="btn btn-craft" @click="runFixAI()" :disabled="craftLoading"><span v-if="craftLoading" class="spinner"></span>一键修复AI味</button>
      </div>
    </div>

    <!-- Fixed Result -->
    <div class="card" v-if="fixedContent">
      <h2>修复结果</h2>
      <div style="margin-bottom:8px"><span class="tag tag-green">已修复</span>以下为去除AI味后的文本：</div>
      <textarea v-model="fixedContent" class="text-area" style="min-height:300px"></textarea>
      <div style="margin-top:8px"><button class="btn btn-save" @click="copyFixed">复制修复文本</button></div>
    </div>

    <!-- Deconstruct Result -->
    <div class="card" v-if="deconstructResult">
      <h2>黄金三章拆解</h2>
      <div v-if="deconstructResult.overall_score" style="margin-bottom:12px">
        <div style="font-size:11px;font-weight:600;margin-bottom:6px">综合评分</div>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:4px">
          <div v-for="(dim, key) in deconstructResult.overall_score" :key="key" style="text-align:center;padding:6px;background:#f8f9fa;border-radius:4px">
            <div style="font-size:16px;font-weight:700;color:var(--primary)">{{ dim }}</div>
            <div style="font-size:9px;color:#888;margin-top:2px">{{ { hook: '开篇', protagonist: '人设', satisfaction: '爽点', world: '世界观', ending: '悬念' }[key] || key }}</div>
          </div>
        </div>
      </div>
      <div v-if="deconstructResult.chapter_1" class="analysis-card">
        <h4>第1章拆解</h4>
        <div style="font-size:11px;line-height:1.8">
          <div><span class="tag tag-blue">钩子</span>{{ deconstructResult.chapter_1.hook_type }} · 效果: {{ deconstructResult.chapter_1.hook_effect }}</div>
          <div style="margin-top:4px"><span class="tag tag-orange">人设</span>{{ deconstructResult.chapter_1.protagonist_method }} · {{ deconstructResult.chapter_1.protagonist_impression }}</div>
          <div style="margin-top:4px"><span class="tag tag-red">爽点</span>{{ deconstructResult.chapter_1.satisfaction_type }} · 铺放比{{ deconstructResult.chapter_1.satisfaction_ratio || '—' }}</div>
          <div style="margin-top:4px"><span class="tag tag-green">悬念</span>{{ deconstructResult.chapter_1.ending_hook }} · 期待度: {{ deconstructResult.chapter_1.ending_expectation }}</div>
        </div>
      </div>
      <div v-if="deconstructResult.chapter_2" class="analysis-card">
        <h4>第2章拆解</h4>
        <div style="font-size:11px;line-height:1.8">
          <div><span class="tag tag-blue">钩子</span>{{ deconstructResult.chapter_2.hook_type || '承接上文' }}</div>
          <div style="margin-top:4px"><span class="tag tag-red">爽点</span>{{ deconstructResult.chapter_2.satisfaction_type || '无' }} · 铺放比{{ deconstructResult.chapter_2.satisfaction_ratio || '—' }}</div>
          <div style="margin-top:4px"><span class="tag tag-green">悬念</span>{{ deconstructResult.chapter_2.ending_hook }}</div>
        </div>
      </div>
      <div v-if="deconstructResult.chapter_3" class="analysis-card">
        <h4>第3章拆解</h4>
        <div style="font-size:11px;line-height:1.8">
          <div><span class="tag tag-red">爽点</span>{{ deconstructResult.chapter_3.satisfaction_type || '无' }} · 铺放比{{ deconstructResult.chapter_3.satisfaction_ratio || '—' }}</div>
          <div style="margin-top:4px"><span class="tag tag-green">悬念</span>{{ deconstructResult.chapter_3.ending_hook }}</div>
        </div>
      </div>
      <div v-if="deconstructResult.key_lessons" class="analysis-card">
        <h4>核心教训</h4>
        <div v-for="(l, i) in deconstructResult.key_lessons" :key="i" style="font-size:11px;color:#555;margin:2px 0">{{ i + 1 }}. {{ l }}</div>
      </div>
      <div v-if="deconstructResult.overall_summary" style="font-size:11px;color:#666;margin-top:8px;font-style:italic">{{ deconstructResult.overall_summary }}</div>
    </div>

    <!-- Quality Score Result -->
    <div class="card" v-if="qualityResult">
      <h2>质量评分报告</h2>
      <div style="display:flex;align-items:center;gap:20px;margin-bottom:14px">
        <div style="text-align:center">
          <div class="score-big" :class="'score-' + qualityResult.grade">{{ qualityResult.total_score }}</div>
          <div style="font-size:14px;font-weight:700" :class="'score-' + qualityResult.grade">评级 {{ qualityResult.grade }}</div>
        </div>
        <div style="flex:1">
          <div style="font-size:12px;color:#555;margin-bottom:6px">{{ qualityResult.verdict }}</div>
          <div v-if="qualityResult.dimensions">
            <div v-for="(dim, key) in qualityResult.dimensions" :key="key" class="bar-chart">
              <span class="bar-label">{{ { opening: '开篇', protagonist: '人设', satisfaction: '爽感', info_push: '信息', cliffhanger: '钩子' }[key] || key }}</span>
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: dim.score + '%', background: dim.score >= 80 ? '#27ae60' : dim.score >= 60 ? '#f1c40f' : '#e74c3c' }"></div>
              </div>
              <span class="bar-value">{{ dim.score }}</span>
            </div>
          </div>
        </div>
      </div>
      <div style="display:flex;gap:12px">
        <div style="flex:1">
          <div style="font-size:11px;font-weight:600;color:#27ae60;margin-bottom:3px">优势</div>
          <div v-for="(s, i) in qualityResult.strengths" :key="i" style="font-size:11px;color:#555;margin:2px 0">&#10003; {{ s }}</div>
        </div>
        <div style="flex:1">
          <div style="font-size:11px;font-weight:600;color:#e74c3c;margin-bottom:3px">短板</div>
          <div v-for="(w, i) in qualityResult.weaknesses" :key="i" style="font-size:11px;color:#555;margin:2px 0">&#10007; {{ w }}</div>
        </div>
      </div>
      <div v-if="qualityResult.suggestions" style="margin-top:8px">
        <div style="font-size:11px;font-weight:600;color:#3498db;margin-bottom:3px">改进建议</div>
        <div v-for="(s, i) in qualityResult.suggestions" :key="i" style="font-size:11px;color:#555;margin:2px 0">{{ i + 1 }}. {{ s }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import ModelSelect from '../components/ModelSelect.vue'
import BookSelector from '../components/BookSelector.vue'
import SourceTabs from '../components/SourceTabs.vue'
import * as downloadApi from '../api/download'
import type { SavedBook } from '../api/client'

const settings = useSettingsStore()

const craftTab = ref('detect')
const craftSource = ref('paste')
const craftText = ref('')
const craftModelIdx = ref(0)
const craftLoading = ref(false)
const savedBooks = ref<SavedBook[]>([])
const selectedCraftBook = ref('')
const detectResult = ref<any>(null)
const fixedContent = ref('')
const deconstructResult = ref<any>(null)
const qualityResult = ref<any>(null)

const sourceTabs = computed(() => {
  if (craftTab.value === 'deconstruct') return [{ label: '粘贴前三章', value: 'paste' }, { label: '选择已下载书籍', value: 'saved' }]
  return [{ label: '粘贴文本', value: 'paste' }, { label: '已下载书籍', value: 'saved' }]
})

const placeholderText = computed(() => {
  if (craftTab.value === 'quality') return '粘贴小说文本（至少1000字，评分准确度随字数增加）...'
  if (craftTab.value === 'deconstruct') return '粘贴小说前三章原文用于拆解黄金三章、钩子设计、爽点节奏...'
  return '粘贴小说文本，检测模板化开头、书面腔、情绪标签化等AI味痕迹...'
})

const scoreClass = computed(() => {
  const s = detectResult.value?.ai_score || 0
  if (s >= 80) return 'S'
  if (s >= 60) return 'A'
  if (s >= 40) return 'B'
  if (s >= 20) return 'C'
  return 'D'
})

function getCraftModel() {
  return settings.models[craftModelIdx.value] || settings.models[0]
}

function onSourceTabChange(val: string) {
  if (val === 'saved') loadSavedBooks()
}

async function loadSavedBooks() {
  try {
    const d = await downloadApi.listSavedBooks()
    savedBooks.value = d.books || []
  } catch {
    savedBooks.value = []
  }
}

async function selectCraftBook(b: SavedBook) {
  selectedCraftBook.value = b.book_id
  try {
    const d = await downloadApi.getBookContent(b.book_id)
    craftText.value = (d.content || '').slice(0, 10000)
  } catch {
    craftText.value = ''
  }
}

async function getCraftContent(): Promise<string> {
  if (craftSource.value === 'saved' && selectedCraftBook.value) {
    const d = await downloadApi.getBookContent(selectedCraftBook.value)
    return d.content || ''
  }
  return craftText.value.trim()
}

async function runDetectAI() {
  const m = getCraftModel()
  if (!m) { alert('请先配置AI模型'); return }
  if (!craftText.value.trim()) { alert('请先输入小说文本'); return }
  craftLoading.value = true
  detectResult.value = null
  fixedContent.value = ''
  try {
    const content = await getCraftContent()
    detectResult.value = await downloadApi.craftDetectApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content })
  } catch (e: any) {
    alert('检测失败: ' + e.message)
  }
  craftLoading.value = false
}

async function runFixAI() {
  const m = getCraftModel()
  if (!m || !detectResult.value) return
  craftLoading.value = true
  try {
    const d = await downloadApi.craftFixApi({
      endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
      content: craftText.value.trim(), issues: detectResult.value.issues || [],
    })
    fixedContent.value = d.content
  } catch (e: any) {
    alert('修复失败: ' + e.message)
  }
  craftLoading.value = false
}

function copyFixed() {
  navigator.clipboard.writeText(fixedContent.value).then(() => alert('已复制到剪贴板'))
}

async function runDeconstruct() {
  const m = getCraftModel()
  if (!m) { alert('请先配置AI模型'); return }
  if (!craftText.value.trim()) { alert('请先输入前三章内容'); return }
  craftLoading.value = true
  deconstructResult.value = null
  try {
    const content = await getCraftContent()
    deconstructResult.value = await downloadApi.craftGoldenThreeApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content })
  } catch (e: any) {
    alert('拆解失败: ' + e.message)
  }
  craftLoading.value = false
}

async function runQualityScore() {
  const m = getCraftModel()
  if (!m) { alert('请先配置AI模型'); return }
  if (!craftText.value.trim()) { alert('请先输入小说文本'); return }
  craftLoading.value = true
  qualityResult.value = null
  try {
    const content = await getCraftContent()
    qualityResult.value = await downloadApi.craftQualityScoreApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content, title: '用户输入', genre: '' })
  } catch (e: any) {
    alert('评分失败: ' + e.message)
  }
  craftLoading.value = false
}

onMounted(() => { loadSavedBooks() })
</script>

<style scoped>
.source-tabs { margin-top: 0; }
</style>
