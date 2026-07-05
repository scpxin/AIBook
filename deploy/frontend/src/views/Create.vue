<template>
  <div>
    <div class="card">
      <h2>AI 小说创作</h2>
      <div class="tip" style="margin-bottom:8px">从灵感到大纲到章节，AI 辅助完成小说创作全流程。点击上方步骤标签可随时切换，所有内容均可自由编辑。</div>

      <div class="project-bar">
        <input v-model="projectStore.projectName" placeholder="项目名称" style="flex:1;min-width:120px;padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:12px" />
        <button class="btn btn-save" style="padding:5px 14px;font-size:12px" @click="saveProject()">💾 保存</button>
        <select v-model="projectStore.selectedProjectId" style="padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:12px;min-width:120px">
          <option value="">-- 选择项目 --</option>
          <option v-for="p in projectStore.projectList" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#11998e;color:#fff" @click="loadProject()" :disabled="!projectStore.selectedProjectId">加载</button>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#e74c3c;color:#fff" @click="deleteProject()" :disabled="!projectStore.selectedProjectId">删除</button>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#ccc;color:#333" @click="newProject()">+ 新建</button>
      </div>

      <StepNav :labels="stepLabels" v-model="novel.step" :has-content="hasStepContent" />

      <!-- Step 0: Inspiration -->
      <div v-show="novel.step === 0">
        <div class="select-row" style="margin-bottom:8px">
          <ModelSelect v-model="novelModelIdx" />
          <button class="btn btn-ai" @click="generateInspire()" :disabled="novel.inspireLoading"><span v-if="novel.inspireLoading" class="spinner"></span>生成灵感</button>
        </div>
        <div style="margin-bottom:10px">
          <div class="select-row" style="margin-bottom:6px">
            <button class="btn btn-ghost" @click="novel.styleExpanded = !novel.styleExpanded">{{ novel.styleExpanded ? '- 收起风格分析' : '+ 参考风格分析（可选）' }}</button>
            <span v-if="novel.styleProfile" style="font-size:10px;color:#11998e;padding:2px 8px;background:#e8f5e9;border-radius:10px">✓ 已分析</span>
          </div>
          <div v-show="novel.styleExpanded">
            <SourceTabs :tabs="styleTabs" v-model="novel.styleTab" @change="onStyleTabChange" />
            <div v-show="novel.styleTab === 'paste'">
              <textarea v-model="novel.styleText" class="text-area" style="min-height:80px;margin-top:6px" placeholder="粘贴小说文本（至少几百字），分析后将自动融入创作..."></textarea>
              <div style="margin-top:6px">
                <button class="btn btn-ai" @click="analyzeStyleText()" :disabled="novel.styleLoading">
                  <span v-if="novel.styleLoading" class="spinner"></span>{{ novel.styleLoading ? '分析中...' : '分析风格' }}
                </button>
              </div>
            </div>
            <div v-show="novel.styleTab === 'saved'">
              <BookSelector :books="novel.savedBooks" v-model="novel.selectedSavedBook" show-action action-text="分析" :loading="novel.savedBookAnalyzing" @select="analyzeSavedBook" />
            </div>
            <div v-if="novel.styleProfile" style="margin-top:6px">
              <div style="font-size:11px;color:#666;margin-bottom:2px">风格摘要：</div>
              <div style="font-size:11px;color:#555;background:#f8f9fa;padding:8px;border-radius:4px;max-height:80px;overflow-y:auto">
                {{ novel.styleProfile.slice(0, 200) }}{{ novel.styleProfile.length > 200 ? '...' : '' }}
              </div>
            </div>
          </div>
        </div>
        <div v-if="novel.inspireError" class="error">{{ novel.inspireError }}</div>
        <div v-for="opt in getInspireTitleOptions()" :key="opt.idx" class="inspire-option" :class="{ selected: opt.selected }" @click="selectInspireTitle(opt)">{{ opt.text }}</div>
        <div v-for="opt in getInspireDescOptions()" :key="opt.idx" class="inspire-option" :class="{ selected: opt.selected }" @click="selectInspireDesc(opt)">{{ opt.text }}</div>
        <div class="select-row" style="margin-top:8px">
          <input v-model="novel.title" placeholder="书名" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
          <input v-model="novel.description" placeholder="简介" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
        </div>
        <div class="select-row" style="margin-top:6px">
          <input v-model="novel.theme" placeholder="主题" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
          <input v-model="novel.genre" placeholder="类型" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
        </div>
        <div class="novel-btn-row">
          <button class="btn btn-dl" @click="novel.step = 1; if (!novel.world) generateWorld()">下一步：构建世界观 &rarr;</button>
        </div>
      </div>

      <!-- Step 1: World -->
      <div v-show="novel.step === 1">
        <div class="tip" style="margin-bottom:6px">世界观设定（可自由编辑）：</div>
        <textarea v-model="novel.world" class="text-area" style="min-height:200px" placeholder="点击「重新生成」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="novel.step = 0">&larr; 上一步：灵感</button>
          <button class="btn btn-ai" @click="generateWorld()">重新生成</button>
          <button class="btn btn-ghost" @click="novel.step = 2">下一步：角色 &rarr;</button>
        </div>
      </div>

      <!-- Step 2: Characters -->
      <div v-show="novel.step === 2">
        <div class="select-row" style="margin-bottom:8px">
          <input v-model.number="novel.charCount" type="number" min="3" max="15" style="width:80px;padding:8px;border:2px solid #e0e0e0;border-radius:6px" />
          <button class="btn btn-ai" @click="generateChars()" :disabled="novel.charsLoading"><span v-if="novel.charsLoading" class="spinner"></span>重新生成角色</button>
        </div>
        <div class="tip" style="margin-bottom:6px">角色设定（每行一个角色，格式：名字 - 身份 - 性格，可自由编辑）：</div>
        <textarea v-model="novel.characters" class="text-area" style="min-height:200px" placeholder="点击「重新生成角色」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="novel.step = 1">&larr; 上一步：世界观</button>
          <button class="btn btn-ghost" @click="novel.step = 3">下一步：大纲 &rarr;</button>
        </div>
      </div>

      <!-- Step 3: Outline -->
      <div v-show="novel.step === 3">
        <div class="select-row" style="margin-bottom:8px">
          <input v-model.number="novel.chapterCount" type="number" min="1" max="20" style="width:80px;padding:8px;border:2px solid #e0e0e0;border-radius:6px" />
          <select v-model="novel.perspective" style="padding:7px;border:1px solid #ddd;border-radius:4px;font-size:12px">
            <option>第三人称</option>
            <option>第一人称</option>
          </select>
          <button class="btn btn-ai" @click="generateOutline()" :disabled="novel.outlineLoading"><span v-if="novel.outlineLoading" class="spinner"></span>重新生成大纲</button>
        </div>
        <div class="tip" style="margin-bottom:6px">章节大纲（每行一章，格式：第X章 标题 - 概要，可自由编辑）：</div>
        <textarea v-model="novel.outlineText" class="text-area" style="min-height:200px" placeholder="点击「重新生成大纲」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="novel.step = 2">&larr; 上一步：角色</button>
          <button class="btn btn-ghost" @click="novel.step = 4">下一步：章节 &rarr;</button>
        </div>
      </div>

      <!-- Step 4: Chapters -->
      <div v-show="novel.step === 4">
        <div class="select-row" style="margin-bottom:8px">
          <input v-model.number="novel.targetWords" type="number" min="500" max="10000" step="500" style="width:100px;padding:8px;border:2px solid #e0e0e0;border-radius:6px" />
          <button class="btn btn-ai" @click="generateNextChapter()" :disabled="novel.chapterLoading"><span v-if="novel.chapterLoading" class="spinner"></span>生成下一章</button>
          <button class="btn btn-save" @click="generateAllChapters()" :disabled="novel.chapterLoading">一键生成全部</button>
          <button v-if="novel.chapterLoading" class="btn" style="background:#e67e22;color:#fff" @click="pauseGeneration">暂停</button>
          <button v-if="novel.chapterPaused" class="btn" style="background:#27ae60;color:#fff" @click="resumeGeneration">继续生成</button>
          <button class="btn btn-save" @click="exportNovel">导出TXT</button>
        </div>
        <div style="margin-bottom:6px">
          <label style="font-size:11px;color:#666;cursor:pointer;display:inline-flex;align-items:center;gap:4px">
            <input type="checkbox" v-model="novel.useCraft" /> 使用网文技法增强
          </label>
        </div>
        <div v-if="novel.chapterProgress" class="tip">{{ novel.chapterProgress }}</div>
        <div v-if="novel.genStatus.total > 0 && novel.chapterLoading" style="margin-bottom:6px">
          <div style="font-size:11px;color:#666;margin-bottom:3px">生成进度: {{ novel.genStatus.completed }}/{{ novel.genStatus.total }} 章 (失败: {{ novel.genStatus.failed }})</div>
          <div style="width:100%;height:6px;background:#eee;border-radius:3px;overflow:hidden">
            <div :style="{ width: (novel.genStatus.completed / novel.genStatus.total * 100) + '%', height: '100%', background: '#11998e', borderRadius: '3px', transition: 'width 0.3s' }"></div>
          </div>
        </div>
        <div style="font-size:11px;color:#888;margin-bottom:6px">已生成 {{ novel.chapters.length }}/{{ novel.outline.length }} 章</div>
        <div v-for="(c, idx) in novel.chapters" :key="idx" style="margin-bottom:10px;border:1px solid #e0e0e0;border-radius:6px;overflow:hidden">
          <div style="background:#f8f9fa;padding:6px 10px;font-weight:600;font-size:12px;display:flex;justify-content:space-between;align-items:center">
            <span>第{{ idx + 1 }}章 {{ novel.outline[idx] ? novel.outline[idx].title : '' }}</span>
            <span style="font-size:10px;color:#888">{{ c.length }}字</span>
          </div>
          <div v-if="!novel.chapterProgress" style="display:flex;gap:4px;padding:4px 10px;background:#f8f9fa;border-top:1px solid #e0e0e0">
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="modals.openRead(idx)">查看完整内容</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="modals.openSettings(idx)">参数设置</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="modals.openPolish(idx, novelModelIdx)">润色</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="modals.openCompare(idx)">对比</button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Style Analysis -->
    <div class="card">
      <h2>AI 风格分析</h2>
      <div class="tip" style="margin-bottom:8px">分析小说的写作风格，为AI仿写提供风格画像。</div>
      <SourceTabs :tabs="analyzeTabs" v-model="novel.analyzeTab" @change="onAnalyzeTabChange" />
      <div v-show="novel.analyzeTab === 'paste'">
        <textarea v-model="novel.analyzeText" class="text-area" placeholder="粘贴小说文本内容..."></textarea>
      </div>
      <div v-show="novel.analyzeTab === 'saved'">
        <BookSelector :books="novel.analyzeSavedBooks" v-model="novel.selectedAnalyzeBook" @select="selectAnalyzeBook" />
        <div v-if="novel.selectedAnalyzeBook && novel.analyzeBookContent" style="margin-top:6px">
          <textarea :value="novel.analyzeBookContent.slice(0, 10000)" class="text-area" style="min-height:100px" readonly></textarea>
        </div>
      </div>
      <div class="select-row" style="margin-top:8px">
        <ModelSelect v-model="analyzeModelIdx" />
        <button class="btn btn-ai" @click="runAnalyze(analyzeModelIdx)" :disabled="novel.analyzeLoading"><span v-if="novel.analyzeLoading" class="spinner"></span>分析</button>
      </div>
      <div v-if="novel.analyzeResult" class="style-profile">
        <h3 style="margin-top:0">风格画像</h3>
        <div v-for="(line, i) in analyzeResultLines" :key="i">
          <h4 v-if="line.match(/^【.+】/)">{{ line }}</h4>
          <p v-else>{{ line }}</p>
        </div>
      </div>
    </div>

    <!-- AI Imitation Generate -->
    <div class="card" v-if="novel.styleProfileForGenerate">
      <h2>AI 仿写生成</h2>
      <ModelSelect v-model="generateModelIdx" />
      <div class="gen-form">
        <div><label>题材类型</label><input v-model="novel.genForm.genre" /></div>
        <div><label>生成章节数</label><input v-model.number="novel.genForm.count" type="number" min="1" max="20" /></div>
        <div class="full"><label>主角设定</label><input v-model="novel.genForm.protagonist" /></div>
        <div class="full"><label>世界观</label><textarea v-model="novel.genForm.world"></textarea></div>
        <div class="full"><label>故事梗概</label><textarea v-model="novel.genForm.outline"></textarea></div>
      </div>
      <div style="margin-top:8px">
        <button class="btn btn-ai" @click="runGenerate(generateModelIdx)" :disabled="novel.genLoading"><span v-if="novel.genLoading" class="spinner"></span>生成</button>
      </div>
      <div v-if="novel.genResult" style="margin-top:8px">
        <div v-for="(ch, i) in getGenChapters()" :key="i" style="margin-bottom:8px">
          <h4>{{ ch.title }} ({{ ch.text.length }}字)</h4>
          <p style="font-size:12px;color:#555">{{ ch.text.slice(0, 200) }}...</p>
        </div>
        <button class="btn btn-save" @click="saveGenerated">保存 TXT</button>
      </div>
    </div>

    <ReadChapterModal />
    <ChapterSettingsModal @apply="onSettingsApply" />
    <PolishCompareModal />
    <CompareModal />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNovelStore } from '../stores/novel'
import { useProjectStore } from '../stores/project'
import { useModalsStore } from '../stores/modals'
import { useSettingsStore } from '../stores/settings'
import StepNav from '../components/StepNav.vue'
import ModelSelect from '../components/ModelSelect.vue'
import BookSelector from '../components/BookSelector.vue'
import SourceTabs from '../components/SourceTabs.vue'
import ReadChapterModal from '../components/modals/ReadChapterModal.vue'
import ChapterSettingsModal from '../components/modals/ChapterSettingsModal.vue'
import PolishCompareModal from '../components/modals/PolishCompareModal.vue'
import CompareModal from '../components/modals/CompareModal.vue'
import {
  generateInspire, getInspireTitleOptions, getInspireDescOptions, selectInspireTitle, selectInspireDesc,
  generateWorld, generateChars, generateOutline,
  generateNextChapter, generateAllChapters, pauseGeneration, resumeGeneration, exportNovel,
  analyzeStyleText, analyzeSavedBook, loadSavedBooks, loadAnalyzeSavedBooks, selectAnalyzeBook,
  runAnalyze, runGenerate, getGenChapters, saveGenerated,
  saveProject, loadProject, deleteProject, newProject,
} from '../actions/novelActions'
import { apiStream } from '../api/client'

const novel = useNovelStore()
const projectStore = useProjectStore()
const modals = useModalsStore()
const settings = useSettingsStore()

const stepLabels = ['1.灵感', '2.世界观', '3.角色', '4.大纲', '5.章节']
const styleTabs = [{label:'粘贴文本',value:'paste'},{label:'已下载书籍',value:'saved'}]
const analyzeTabs = [{label:'粘贴文本',value:'paste'},{label:'已下载书籍',value:'saved'}]
const novelModelIdx = ref(0)
const analyzeModelIdx = ref(0)
const generateModelIdx = ref(0)

const analyzeResultLines = computed(() => novel.analyzeResult.split('\n').filter(l => l.trim()))

function hasStepContent(i: number) {
  if (i === 0) return !!(novel.title || novel.description)
  if (i === 1) return !!novel.world
  if (i === 2) return !!novel.characters
  if (i === 3) return !!novel.outlineText
  if (i === 4) return novel.chapters.length > 0
  return false
}

function onStyleTabChange(val: string) { if (val === 'saved') loadSavedBooks() }
function onAnalyzeTabChange(val: string) { if (val === 'saved') loadAnalyzeSavedBooks() }

function onSettingsApply(idx: number, target: number, extra: string) {
  if (idx >= novel.chapters.length) return
  novel.chapterLoading = true
  novel.chapterProgress = '正在重生成第' + (idx + 1) + '章...'
  const outlineItem = novel.outline[idx]
  const outlineText = novel.outline.map(o => o.title + ' - ' + o.summary).join('\n')
  const prevChapters = novel.chapters.slice(0, idx).map((c, i) => '第' + (i + 1) + '章 ' + (novel.outline[i]?.title || '') + '\n' + c).join('\n\n')
  const prompt = '请根据以下信息重写第' + (idx + 1) + '章' + (outlineItem?.title ? '《' + outlineItem.title + '》' : '') + '\n\n大纲概要：' + (outlineItem ? outlineItem.summary : '') + '\n全书大纲：\n' + outlineText + '\n\n已有章节内容：\n' + prevChapters + '\n\n本章目标字数：' + target + '字' + (extra ? '\n\n特殊要求：' + extra : '') + '\n\n只输出本章正文内容，不要任何解释或前缀'
  const model = settings.models[novelModelIdx.value] || settings.models[0]
  apiStream(
    '/api/generate_chapter_stream',
    { model: { name: model.name, endpoint: model.endpoint, apiKey: model.apiKey, model: model.model }, prompt, target_words: target, temperature: 0.7, max_tokens: Math.min(target * 2, 16000) },
    (text: string) => { novel.chapters[idx] = (novel.chapters[idx] || '') + text },
    () => { novel.chapterLoading = false; novel.chapterProgress = '重生成完成' },
    (err: string) => { novel.chapterLoading = false; novel.chapterProgress = '错误: ' + err }
  )
}

onMounted(() => { projectStore.loadList() })
</script>

<style scoped>
.project-bar {
  margin-bottom: 8px; padding: 8px; background: #f0f7ff;
  border-radius: 6px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
</style>
