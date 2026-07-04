<template>
  <div>
    <div class="card">
      <h2>AI 小说创作</h2>
      <div class="tip" style="margin-bottom:8px">从灵感到大纲到章节，AI 辅助完成小说创作全流程。点击上方步骤标签可随时切换，所有内容均可自由编辑。</div>

      <!-- Project save/load -->
      <div style="margin-bottom:8px;padding:8px;background:#f0f7ff;border-radius:6px;display:flex;align-items:center;gap:6px;flex-wrap:wrap">
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

      <!-- Step indicators -->
      <div class="novel-steps">
        <div v-for="(s, i) in stepLabels" :key="i" class="novel-step" :class="{ active: novel.step === i, done: hasStepContent(i) }" @click="showStep(i)">{{ s }}</div>
      </div>

      <!-- Step 0: Inspiration -->
      <div v-show="novel.step === 0">
        <div class="select-row" style="margin-bottom:8px">
          <select v-model="novelModelIdx" style="flex:1;padding:7px;border:1px solid #ddd;border-radius:4px;font-size:12px">
            <option v-for="(m, i) in settings.models" :key="m.id" :value="i">{{ m.name }}</option>
          </select>
          <button class="btn btn-ai" @click="generateInspire()" :disabled="inspireLoading"><span v-if="inspireLoading" class="spinner"></span>生成灵感</button>
        </div>

        <!-- Style analysis (optional) -->
        <div style="margin-bottom:10px">
          <div class="select-row" style="margin-bottom:6px">
            <button class="btn btn-ghost" @click="styleExpanded = !styleExpanded">{{ styleExpanded ? '- 收起风格分析' : '+ 参考风格分析（可选）' }}</button>
            <span v-if="novel.styleProfile" style="font-size:10px;color:#11998e;padding:2px 8px;background:#e8f5e9;border-radius:10px">✓ 已分析</span>
          </div>
          <div v-show="styleExpanded">
            <div class="source-tabs">
              <div class="source-tab" :class="{ active: styleTab === 'paste' }" @click="styleTab = 'paste'">粘贴文本</div>
              <div class="source-tab" :class="{ active: styleTab === 'saved' }" @click="styleTab = 'saved'; loadSavedBooks()">已下载书籍</div>
            </div>
            <div v-show="styleTab === 'paste'">
              <textarea v-model="styleText" class="text-area" style="min-height:80px;margin-top:6px" placeholder="粘贴小说文本（至少几百字），分析后将自动融入创作..."></textarea>
              <div style="margin-top:6px">
                <button class="btn btn-ai" @click="analyzeStyleText()" :disabled="styleLoading">
                  <span v-if="styleLoading" class="spinner"></span>{{ styleLoading ? '分析中...' : '分析风格' }}
                </button>
              </div>
            </div>
            <div v-show="styleTab === 'saved'">
              <div v-for="b in savedBooks" :key="b.book_id" class="book-item" :class="{ selected: selectedSavedBook === b.book_id }" @click="analyzeSavedBook(b)">
                <div>
                  <div class="book-title">{{ b.title }}</div>
                  <div class="book-meta">{{ b.book_id }} | {{ b.total || 0 }} 章 | {{ Math.round(b.size / 1024) }}KB</div>
                </div>
                <button class="btn btn-ai" style="padding:4px 12px;font-size:11px" :disabled="savedBookAnalyzing">
                  {{ selectedSavedBook === b.book_id && savedBookAnalyzing ? '分析中...' : '分析' }}
                </button>
              </div>
              <div v-if="!savedBooks.length" class="empty">暂无已下载书籍</div>
            </div>
            <div v-if="novel.styleProfile" style="margin-top:6px">
              <div style="font-size:11px;color:#666;margin-bottom:2px">风格摘要：</div>
              <div style="font-size:11px;color:#555;background:#f8f9fa;padding:8px;border-radius:4px;max-height:80px;overflow-y:auto">
                {{ novel.styleProfile.slice(0, 200) }}{{ novel.styleProfile.length > 200 ? '...' : '' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="inspireError" class="error">{{ inspireError }}</div>
        <div v-for="opt in inspireTitleOptions" :key="opt.idx" class="inspire-option" :class="{ selected: opt.selected }" @click="selectInspireTitle(opt)">{{ opt.text }}</div>
        <div v-for="opt in inspireDescOptions" :key="opt.idx" class="inspire-option" :class="{ selected: opt.selected }" @click="selectInspireDesc(opt)">{{ opt.text }}</div>
        <div class="select-row" style="margin-top:8px">
          <input v-model="novel.title" placeholder="书名" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
          <input v-model="novel.description" placeholder="简介" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
        </div>
        <div class="select-row" style="margin-top:6px">
          <input v-model="novel.theme" placeholder="主题" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
          <input v-model="novel.genre" placeholder="类型" style="flex:1;padding:8px 12px;border:2px solid #e0e0e0;border-radius:6px;font-size:13px" />
        </div>
        <div class="novel-btn-row">
          <button class="btn btn-dl" @click="showStep(1); if (!novel.world) generateWorld()">下一步：构建世界观 &rarr;</button>
        </div>
      </div>

      <!-- Step 1: World -->
      <div v-show="novel.step === 1">
        <div class="tip" style="margin-bottom:6px">世界观设定（可自由编辑）：</div>
        <textarea v-model="novel.world" class="text-area" style="min-height:200px" placeholder="点击「重新生成」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="showStep(0)">&larr; 上一步：灵感</button>
          <button class="btn btn-ai" @click="generateWorld()">重新生成</button>
          <button class="btn btn-ghost" @click="showStep(2)">下一步：角色 &rarr;</button>
        </div>
      </div>

      <!-- Step 2: Characters -->
      <div v-show="novel.step === 2">
        <div class="select-row" style="margin-bottom:8px">
          <input v-model.number="novel.charCount" type="number" min="3" max="15" style="width:80px;padding:8px;border:2px solid #e0e0e0;border-radius:6px" />
          <button class="btn btn-ai" @click="generateChars()" :disabled="charsLoading"><span v-if="charsLoading" class="spinner"></span>重新生成角色</button>
        </div>
        <div class="tip" style="margin-bottom:6px">角色设定（每行一个角色，格式：名字 - 身份 - 性格，可自由编辑）：</div>
        <textarea v-model="novel.characters" class="text-area" style="min-height:200px" placeholder="点击「重新生成角色」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="showStep(1)">&larr; 上一步：世界观</button>
          <button class="btn btn-ghost" @click="showStep(3)">下一步：大纲 &rarr;</button>
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
          <button class="btn btn-ai" @click="generateOutline()" :disabled="outlineLoading"><span v-if="outlineLoading" class="spinner"></span>重新生成大纲</button>
        </div>
        <div class="tip" style="margin-bottom:6px">章节大纲（每行一章，格式：第X章 标题 - 概要，可自由编辑）：</div>
        <textarea v-model="novel.outlineText" class="text-area" style="min-height:200px" placeholder="点击「重新生成大纲」按钮自动生成，或直接在此输入..."></textarea>
        <div class="novel-btn-row">
          <button class="btn btn-ghost" @click="showStep(2)">&larr; 上一步：角色</button>
          <button class="btn btn-ghost" @click="showStep(4)">下一步：章节 &rarr;</button>
        </div>
      </div>

      <!-- Step 4: Chapters -->
      <div v-show="novel.step === 4">
        <div class="select-row" style="margin-bottom:8px">
          <input v-model.number="novel.targetWords" type="number" min="500" max="10000" step="500" style="width:100px;padding:8px;border:2px solid #e0e0e0;border-radius:6px" />
          <button class="btn btn-ai" @click="generateNextChapter()" :disabled="chapterLoading"><span v-if="chapterLoading" class="spinner"></span>生成下一章</button>
          <button class="btn btn-save" @click="generateAllChapters()" :disabled="chapterLoading">一键生成全部</button>
          <button v-if="chapterLoading" class="btn" style="background:#e67e22;color:#fff" @click="pauseGeneration">暂停</button>
          <button v-if="chapterPaused" class="btn" style="background:#27ae60;color:#fff" @click="resumeGeneration">继续生成</button>
          <button class="btn btn-save" @click="exportNovel">导出TXT</button>
        </div>
        <div style="margin-bottom:6px">
          <label style="font-size:11px;color:#666;cursor:pointer;display:inline-flex;align-items:center;gap:4px">
            <input type="checkbox" v-model="novel.useCraft" /> 使用网文技法增强（融入钩子设计、爽点节奏、去AI味）
          </label>
        </div>
        <div v-if="chapterProgress" class="tip">{{ chapterProgress }}</div>
        <div v-if="genStatus.total > 0 && chapterLoading" style="margin-bottom:6px">
          <div style="font-size:11px;color:#666;margin-bottom:3px">生成进度: {{ genStatus.completed }}/{{ genStatus.total }} 章 (失败: {{ genStatus.failed }})</div>
          <div style="width:100%;height:6px;background:#eee;border-radius:3px;overflow:hidden">
            <div :style="{ width: (genStatus.completed / genStatus.total * 100) + '%', height: '100%', background: '#11998e', borderRadius: '3px', transition: 'width 0.3s' }"></div>
          </div>
        </div>
        <div style="font-size:11px;color:#888;margin-bottom:6px">已生成 {{ novel.chapters.length }}/{{ novel.outline.length }} 章（点击章节内容可编辑）</div>
        <div v-for="(c, idx) in novel.chapters" :key="idx" style="margin-bottom:10px;border:1px solid #e0e0e0;border-radius:6px;overflow:hidden">
          <div style="background:#f8f9fa;padding:6px 10px;font-weight:600;font-size:12px;display:flex;justify-content:space-between;align-items:center">
            <span>第{{ idx + 1 }}章 {{ novel.outline[idx] ? novel.outline[idx].title : '' }}</span>
            <span style="font-size:10px;color:#888">{{ c.length }}字</span>
          </div>
          <div v-if="!chapterProgress" style="display:flex;gap:4px;padding:4px 10px;background:#f8f9fa;border-top:1px solid #e0e0e0">
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="openReadChapter(idx)">查看完整内容</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="openChapterSettings(idx)">参数设置</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="polishChapter(idx)">润色</button>
            <button class="btn" style="padding:2px 10px;font-size:11px" @click="openCompare(idx)">对比</button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Style Analysis (standalone) -->
    <div class="card">
      <h2>AI 风格分析</h2>
      <div class="tip" style="margin-bottom:8px">分析小说的写作风格，为AI仿写提供风格画像。</div>
      <div class="source-tabs">
        <div class="source-tab" :class="{ active: analyzeTab === 'paste' }" @click="analyzeTab = 'paste'">粘贴文本</div>
        <div class="source-tab" :class="{ active: analyzeTab === 'saved' }" @click="analyzeTab = 'saved'; loadAnalyzeSavedBooks()">已下载书籍</div>
      </div>
      <div v-show="analyzeTab === 'paste'">
        <textarea v-model="analyzeText" class="text-area" placeholder="粘贴小说文本内容（至少几百字），AI将分析其写作风格..."></textarea>
      </div>
      <div v-show="analyzeTab === 'saved'">
        <div v-for="b in analyzeSavedBooks" :key="b.book_id" class="book-item" :class="{ selected: selectedAnalyzeBook === b.book_id }" @click="selectAnalyzeBook(b)">
          <div>
            <div class="book-title">{{ b.title }}</div>
            <div class="book-meta">{{ b.book_id }} | {{ b.total || 0 }} 章 | {{ Math.round(b.size / 1024) }}KB</div>
          </div>
          <button class="btn btn-ai" style="padding:4px 12px;font-size:11px">选择</button>
        </div>
        <div v-if="selectedAnalyzeBook && analyzeBookContent" style="margin-top:6px">
          <textarea :value="analyzeBookContent.slice(0, 10000)" class="text-area" style="min-height:100px" readonly></textarea>
        </div>
      </div>
      <div class="select-row" style="margin-top:8px">
        <select v-model="analyzeModelIdx" style="flex:1;padding:7px;border:1px solid #ddd;border-radius:4px;font-size:12px">
          <option v-for="(m, i) in settings.models" :key="m.id" :value="i">{{ m.name }}</option>
        </select>
        <button class="btn btn-ai" @click="runAnalyze()" :disabled="analyzeLoading"><span v-if="analyzeLoading" class="spinner"></span>分析</button>
      </div>
      <div v-if="analyzeResult" class="style-profile">
        <h3 style="margin-top:0">风格画像</h3>
        <div v-for="(line, i) in analyzeResultLines" :key="i">
          <h4 v-if="line.match(/^【.+】/)">{{ line }}</h4>
          <p v-else>{{ line }}</p>
        </div>
      </div>
    </div>

    <!-- AI Imitation Generate -->
    <div class="card" v-if="styleProfile">
      <h2>AI 仿写生成</h2>
      <div class="select-row">
        <select v-model="generateModelIdx" style="flex:1;padding:7px;border:1px solid #ddd;border-radius:4px;font-size:12px">
          <option v-for="(m, i) in settings.models" :key="m.id" :value="i">{{ m.name }}</option>
        </select>
      </div>
      <div class="gen-form">
        <div><label>题材类型</label><input v-model="genForm.genre" placeholder="悬疑 / 玄幻..." /></div>
        <div><label>生成章节数</label><input v-model.number="genForm.count" type="number" min="1" max="20" /></div>
        <div class="full"><label>主角设定</label><input v-model="genForm.protagonist" placeholder="姓名、年龄、身份..." /></div>
        <div class="full"><label>世界观</label><textarea v-model="genForm.world" placeholder="时代背景、势力分布..."></textarea></div>
        <div class="full"><label>故事梗概</label><textarea v-model="genForm.outline" placeholder="主线剧情..."></textarea></div>
      </div>
      <div style="margin-top:8px">
        <button class="btn btn-ai" @click="runGenerate()" :disabled="genLoading"><span v-if="genLoading" class="spinner"></span>生成</button>
      </div>
      <div v-if="genResult" style="margin-top:8px">
        <div v-for="(ch, i) in genChapters" :key="i" style="margin-bottom:8px">
          <h4>{{ ch.title }} ({{ ch.text.length }}字)</h4>
          <p style="font-size:12px;color:#555">{{ ch.text.slice(0, 200) }}...</p>
        </div>
        <button class="btn btn-save" @click="saveGenerated">保存 TXT</button>
      </div>
    </div>

    <!-- Read Chapter Modal -->
    <div v-if="showReadModal" class="modal-overlay" @click.self="showReadModal = false">
      <div class="modal-card" style="max-width:1000px;width:90vw">
        <button class="modal-close" @click="showReadModal = false">&times;</button>
        <h3>{{ readModalTitle }}</h3>
        <textarea v-model="readModalContent" class="chapter-detail" style="width:100%;min-height:500px;padding:12px;font-size:14px;line-height:1.8;font-family:inherit;resize:vertical;box-sizing:border-box"></textarea>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="btn btn-ai" style="flex:1" @click="saveReadModal">保存修改</button>
          <button class="btn" style="flex:1;background:#ccc;color:#333" @click="showReadModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- Chapter Settings Modal -->
    <div v-if="showSettingsModal" class="modal-overlay" @click.self="showSettingsModal = false">
      <div class="modal-card" style="max-width:480px">
        <button class="modal-close" @click="showSettingsModal = false">&times;</button>
        <h3>章节参数设置 - 第{{ settingsModalIdx + 1 }}章</h3>
        <div class="form-group"><label>目标字数</label><input v-model.number="settingsForm.targetWords" type="number" min="500" max="20000" step="500" /></div>
        <div class="form-group"><label>额外提示词（可选）</label><input v-model="settingsForm.extraPrompt" placeholder="如：增加打斗描写、突出主角智慧" /></div>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="btn btn-ai" style="flex:1" @click="applyChapterSettings">应用并重生成</button>
          <button class="btn" style="flex:1;background:#ccc;color:#333" @click="showSettingsModal = false">取消</button>
        </div>
      </div>
    </div>

    <!-- Polish/Compare Modal -->
    <div v-if="showCompareModal" class="modal-overlay" @click.self="showCompareModal = false">
      <div class="modal-card" style="max-width:1200px;width:95vw">
        <button class="modal-close" @click="showCompareModal = false">&times;</button>
        <h3>AI 润色 - 第{{ compareIdx + 1 }}章</h3>
        <div style="display:flex;height:100%;gap:8px;margin-top:8px">
          <textarea v-model="compareOriginal" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit"></textarea>
          <textarea v-model="comparePolished" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit" readonly></textarea>
        </div>
        <div style="font-size:11px;color:#666;margin-top:4px">{{ polishLoadingTip }}</div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn" style="flex:1;background:#11998e;color:#fff" @click="applyPolish">采用润色版</button>
          <button class="btn" style="flex:1;background:#ccc;color:#333" @click="showCompareModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { useProjectStore } from '../stores/project'
import * as novelApi from '../api/novel'
import * as chapterApi from '../api/chapter'
import * as outlineApi from '../api/outline'
import * as downloadApi from '../api/download'
import type { SavedBook } from '../api/client'
import { apiStream } from '../api/client'

const settings = useSettingsStore()
const projectStore = useProjectStore()

const stepLabels = ['1.灵感', '2.世界观', '3.角色', '4.大纲', '5.章节']

const novel = reactive({
  step: 0,
  title: '',
  description: '',
  theme: '',
  genre: '',
  world: '',
  characters: '',
  outlineText: '',
  outline: [] as any[],
  chapters: [] as string[],
  currentChapter: 0,
  charCount: 6,
  chapterCount: 3,
  perspective: '第三人称',
  targetWords: 3000,
  styleProfile: '',
  useCraft: true,
})

const novelModelIdx = ref(0)
const inspireLoading = ref(false)
const inspireError = ref('')
const inspireTitleOptions = ref<any[]>([])
const inspireDescOptions = ref<any[]>([])
const charsLoading = ref(false)
const outlineLoading = ref(false)
const chapterLoading = ref(false)
const chapterProgress = ref('')
const chapterPaused = ref(false)
const chapterPauseIdx = ref(0)
const genStatus = ref({ total: 0, completed: 0, failed: 0, current: 0 })

const styleExpanded = ref(false)
const styleTab = ref('paste')
const styleText = ref('')
const styleLoading = ref(false)
const savedBooks = ref<SavedBook[]>([])
const selectedSavedBook = ref('')
const savedBookAnalyzing = ref(false)

const analyzeTab = ref('paste')
const analyzeText = ref('')
const analyzeModelIdx = ref(0)
const analyzeLoading = ref(false)
const analyzeResult = ref('')
const analyzeResultLines = computed(() => analyzeResult.value.split('\n').filter(l => l.trim()))
const analyzeSavedBooks = ref<SavedBook[]>([])
const selectedAnalyzeBook = ref('')
const analyzeBookContent = ref('')
const styleProfile = ref('')

const generateModelIdx = ref(0)
const genForm = reactive({ genre: '', count: 3, protagonist: '', world: '', outline: '' })
const genLoading = ref(false)
const genResult = ref('')

const genChapters = computed(() => {
  if (!genResult.value) return []
  const chapters: any[] = []
  const re = /第([一-龥\d]+)章\s*(.*?)(?:\n|$)/g
  let match
  let lastIdx = 0
  while ((match = re.exec(genResult.value)) !== null) {
    if (lastIdx > 0) chapters[chapters.length - 1].text = genResult.value.slice(lastIdx, match.index).trim()
    chapters.push({ title: '第' + match[1] + '章' + (match[2] ? ' ' + match[2] : ''), text: '' })
    lastIdx = match.index + match[0].length
  }
  if (chapters.length && lastIdx < genResult.value.length) {
    chapters[chapters.length - 1].text = genResult.value.slice(lastIdx).trim()
  }
  return chapters
})

const showReadModal = ref(false)
const readModalTitle = ref('')
const readModalContent = ref('')
const readModalIdx = ref(0)

const showSettingsModal = ref(false)
const settingsModalIdx = ref(0)
const settingsForm = reactive({ targetWords: 3000, extraPrompt: '' })

const showCompareModal = ref(false)
const compareIdx = ref(0)
const compareOriginal = ref('')
const comparePolished = ref('')
const polishLoadingTip = ref('正在润色中，请稍候...')

function getNovelModel() {
  return settings.models[novelModelIdx.value] || settings.models[0]
}

function showStep(n: number) {
  novel.step = n
}

function hasStepContent(i: number) {
  if (i === 0) return !!(novel.title || novel.description)
  if (i === 1) return !!novel.world
  if (i === 2) return !!novel.characters
  if (i === 3) return !!novel.outlineText
  if (i === 4) return novel.chapters.length > 0
  return false
}

async function loadSavedBooks() {
  try {
    const d = await downloadApi.listSavedBooks()
    savedBooks.value = d.books || []
  } catch {
    savedBooks.value = []
  }
}

async function loadAnalyzeSavedBooks() {
  try {
    const d = await downloadApi.listSavedBooks()
    analyzeSavedBooks.value = d.books || []
  } catch {
    analyzeSavedBooks.value = []
  }
}

async function selectAnalyzeBook(b: SavedBook) {
  selectedAnalyzeBook.value = b.book_id
  try {
    const d = await downloadApi.getBookContent(b.book_id)
    analyzeBookContent.value = d.content || ''
    analyzeText.value = (d.content || '').slice(0, 10000)
  } catch {
    analyzeBookContent.value = ''
  }
}

async function analyzeStyleText() {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  if (!styleText.value.trim()) { alert('请先粘贴小说文本'); return }
  styleLoading.value = true
  try {
    const d = await novelApi.analyzeStyleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: styleText.value.trim() })
    novel.styleProfile = d.result || ''
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  styleLoading.value = false
}

async function analyzeSavedBook(b: SavedBook) {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  selectedSavedBook.value = b.book_id
  savedBookAnalyzing.value = true
  try {
    const d = await downloadApi.getBookContent(b.book_id)
    const content = d.content || ''
    const r = await novelApi.analyzeStyleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content })
    novel.styleProfile = r.result || ''
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  savedBookAnalyzing.value = false
}

async function generateInspire() {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  inspireLoading.value = true
  inspireError.value = ''
  inspireTitleOptions.value = []
  inspireDescOptions.value = []

  try {
    const d1 = await novelApi.inspirationTitleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, styleProfile: novel.styleProfile })
    inspireTitleOptions.value = (d1.options || []).map((opt: any, i: number) => ({
      idx: i,
      text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || JSON.stringify(opt)) : opt,
      selected: i === 0,
    }))
    if (d1.options && d1.options[0]) {
      const first = d1.options[0]
      novel.title = typeof first === 'object' ? (first.name || first.title || first.text || JSON.stringify(first)) : first
    }

    const d2 = await novelApi.inspirationDescriptionApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, styleProfile: novel.styleProfile })
    inspireDescOptions.value = (d2.options || []).map((opt: any, i: number) => ({
      idx: i,
      text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || opt.description || JSON.stringify(opt)) : opt,
      selected: i === 0,
    }))
    if (d2.options && d2.options[0]) {
      const first = d2.options[0]
      novel.description = typeof first === 'object' ? (first.name || first.title || first.text || first.description || JSON.stringify(first)) : first
    }

    const d3 = await novelApi.inspirationThemeApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, description: novel.description, styleProfile: novel.styleProfile })
    if (d3.options && d3.options[0]) {
      const first = d3.options[0]
      novel.theme = typeof first === 'object' ? (first.name || first.title || first.text || first.theme || JSON.stringify(first)) : first
    }

    const d4 = await novelApi.inspirationGenreApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, description: novel.description, styleProfile: novel.styleProfile })
    if (d4.options && d4.options[0]) {
      const first = d4.options[0]
      novel.genre = typeof first === 'object' ? (first.name || first.title || first.text || first.genre || JSON.stringify(first)) : first
    }

    await saveStepSummary('inspiration', {
      title: novel.title,
      description: novel.description,
      theme: novel.theme,
      genre: novel.genre,
    })
  } catch (e: any) {
    inspireError.value = e.message
  }
  inspireLoading.value = false
}

function selectInspireTitle(opt: any) {
  inspireTitleOptions.value.forEach(o => o.selected = false)
  opt.selected = true
  novel.title = opt.text
}

function selectInspireDesc(opt: any) {
  inspireDescOptions.value.forEach(o => o.selected = false)
  opt.selected = true
  novel.description = opt.text
}

async function generateWorld() {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.world = '正在生成世界观，请稍候...'
  try {
    const description = (novel.styleProfile ? '[风格参考]\n' + novel.styleProfile + '\n\n[故事简介]\n' : '') + novel.description
    const d = await novelApi.worldbuildingApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, theme: novel.theme, genre: novel.genre, description, styleProfile: novel.styleProfile })
    let text = ''
    const labels: Record<string, string> = { time_period: '【时间背景】', location: '【空间环境】', atmosphere: '【情感基调】', rules: '【世界规则】' }
    ;['time_period', 'location', 'atmosphere', 'rules'].forEach(k => {
      if (d.world?.[k]) {
        let val = d.world[k]
        if (typeof val === 'object') {
          val = val.description || val.detail || val.content || val.name || JSON.stringify(val)
        }
        text += labels[k] + '\n' + val + '\n\n'
      }
    })
    novel.world = text.trim()
    await saveStepSummary('world', { world: novel.world })
  } catch (e: any) {
    novel.world = '生成失败: ' + e.message
  }
}

async function generateChars() {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  charsLoading.value = true
  novel.characters = '正在生成角色，请稍候...'
  try {
    const theme = novel.theme + (novel.styleProfile ? '\n\n[风格参考]\n' + novel.styleProfile : '')
    const d = await novelApi.charactersApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, worldData: { rules: novel.world }, theme, genre: novel.genre, count: novel.charCount, styleProfile: novel.styleProfile })
    let text = ''
    ;(d.characters || []).forEach((c: any) => {
      if (c.is_organization) {
        text += (c.name || '') + ' - 组织 - ' + (c.organization_purpose || '') + '\n'
      } else {
        text += (c.name || '') + ' - ' + (c.role_type || '角色') + ' - ' + (c.personality || '') + '\n'
      }
    })
    novel.characters = text.trim()
    await saveStepSummary('characters', { characters: novel.characters })
  } catch (e: any) {
    novel.characters = '生成失败: ' + e.message
  }
  charsLoading.value = false
}

async function loadStepSummaries() {
  if (!projectStore.currentProjectId) return {}
  try {
    const r = await novelApi.stepSummaryGetApi(projectStore.currentProjectId)
    return r.summaries || {}
  } catch {
    return {}
  }
}

async function saveStepSummary(step: string, summaryData: any) {
  if (!projectStore.currentProjectId) return
  try {
    await novelApi.stepSummarySaveApi({ projectId: projectStore.currentProjectId, step, summary: summaryData })
  } catch {
    console.error('步骤摘要保存失败')
  }
}

async function generateOutline() {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  outlineLoading.value = true
  novel.outlineText = '正在生成大纲，请稍候...'
  try {
    const summaries = await loadStepSummaries()
    const summaryParts: string[] = []
    if (summaries.inspiration) {
      const ins = summaries.inspiration
      summaryParts.push('[灵感步骤] 标题: ' + (ins.title || '') + ' | 简介: ' + (ins.description || '') + ' | 主题: ' + (ins.theme || '') + ' | 类型: ' + (ins.genre || ''))
    }
    if (summaries.world) {
      summaryParts.push('[世界观步骤] ' + (summaries.world.world || '').slice(0, 500))
    }
    if (summaries.characters) {
      summaryParts.push('[角色步骤] ' + (summaries.characters.characters || '').slice(0, 500))
    }
    const stepContext = summaryParts.length > 0 ? '\n\n[前期步骤摘要]\n' + summaryParts.join('\n') : ''
    const title = novel.title + (novel.styleProfile ? '\n\n[风格参考]\n' + novel.styleProfile : '') + stepContext
    const d = await novelApi.outlineApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title, theme: novel.theme, genre: novel.genre, charactersInfo: novel.characters, chapterCount: novel.chapterCount, narrativePerspective: novel.perspective, styleProfile: novel.styleProfile })
    const outline = d.outline || []
    let text = ''
    outline.forEach((o: any) => {
      text += '第' + o.chapter_number + '章 ' + (o.title || '') + ' - ' + (o.summary || '') + '\n'
    })
    novel.outlineText = text.trim()
    parseOutline()
    await saveOutlineToDb()
    await saveStepSummary('outline', { outlineText: novel.outlineText, outline: novel.outline })
  } catch (e: any) {
    novel.outlineText = '生成失败: ' + e.message
  }
  outlineLoading.value = false
}

function parseOutline() {
  const text = novel.outlineText.trim()
  if (!text) { novel.outline = []; return }
  const lines = text.split('\n').filter(l => l.trim())
  novel.outline = lines.map((line: string, i: number) => {
    const m = line.match(/第([一-龥\d]+)章\s*(.*)/)
    if (m) return { chapter_number: m[1], title: m[1], summary: m[2] || '' }
    return { chapter_number: String(i + 1), title: line.slice(0, 30), summary: line }
  })
}

async function saveOutlineToDb() {
  if (!projectStore.currentProjectId) return
  if (!novel.outline || novel.outline.length === 0) return
  for (const o of novel.outline) {
    try {
      await outlineApi.saveOutlineApi({
        projectId: projectStore.currentProjectId,
        chapterNumber: typeof o.chapter_number === 'string' ? parseInt(o.chapter_number) || 1 : o.chapter_number,
        title: o.title || '',
        summary: o.summary || '',
        status: 'done',
      })
    } catch (e: any) {
      console.error('大纲保存失败:', e.message)
    }
  }
}

async function loadOutlinesFromDb() {
  if (!projectStore.currentProjectId) return
  try {
    const r = await outlineApi.getOutlinesApi(projectStore.currentProjectId)
    if (r.outlines && Array.isArray(r.outlines) && r.outlines.length > 0) {
      const outlineItems = r.outlines.sort((a: any, b: any) => a.chapter_number - b.chapter_number)
      novel.outline = outlineItems.map((o: any) => ({
        chapter_number: o.chapter_number,
        title: o.title || ('第' + o.chapter_number + '章'),
        summary: o.summary || '',
      }))
      let text = ''
      outlineItems.forEach((o: any) => {
        text += '第' + o.chapter_number + '章 ' + (o.title || '') + ' - ' + (o.summary || '') + '\n'
      })
      novel.outlineText = text.trim()
    }
  } catch (e: any) {
    console.error('加载大纲失败:', e.message)
  }
}

async function loadChaptersFromDb() {
  if (!projectStore.currentProjectId) return
  try {
    const r = await chapterApi.getChaptersApi(projectStore.currentProjectId)
    if (r.chapters && Array.isArray(r.chapters)) {
      for (const ch of r.chapters) {
        const idx = ch.chapter_number - 1
        if (ch.status === 'done' && ch.content && idx < novel.outline.length) {
          if (!novel.chapters[idx] || novel.chapters[idx].length < 100) {
            novel.chapters[idx] = ch.content
          }
        }
      }
    }
  } catch (e: any) {
    console.error('加载章节失败:', e.message)
  }
}

async function generateNextChapter() {
  parseOutline()
  if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return }
  if (novel.chapters.length >= novel.outline.length) { alert('所有章节已生成完毕'); return }
  if (!projectStore.currentProjectId) {
    const autoName = novel.title || '未命名项目'
    projectStore.projectName = autoName
    await saveProject()
  }
  await generateOneChapter(novel.chapters.length)
}

async function generateAllChapters() {
  parseOutline()
  if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return }
  if (!projectStore.currentProjectId) {
    const autoName = novel.title || '未命名项目'
    projectStore.projectName = autoName
    await saveProject()
  }
  await loadChaptersFromDb()
  let startIdx = novel.chapters.length
  for (let i = 0; i < novel.outline.length; i++) {
    if (i < novel.chapters.length && novel.chapters[i] && novel.chapters[i].length > 100) {
      continue
    }
    startIdx = i
    break
  }
  if (startIdx >= novel.outline.length) {
    alert('所有章节已生成完毕')
    return
  }
  try {
    await chapterApi.startGenerationApi(projectStore.currentProjectId, novel.outline.length)
  } catch { /* ignore */ }
  genStatus.value = { total: novel.outline.length, completed: startIdx, failed: 0, current: startIdx + 1 }
  let i = startIdx
  chapterPaused.value = false
  chapterPauseIdx.value = i

  async function next() {
    if (chapterPaused.value) { chapterPauseIdx.value = i; return }
    if (i >= novel.outline.length) { genStatus.value.current = 0; return }
    if (i < novel.chapters.length && novel.chapters[i] && novel.chapters[i].length > 100) { i++; next(); return }
    genStatus.value.current = i + 1
    const success = await generateOneChapter(i)
    if (chapterPaused.value) { chapterPauseIdx.value = i; return }
    if (novel.chapters[i] && novel.chapters[i].length > 100) {
      genStatus.value.completed++
    } else {
      genStatus.value.failed++
    }
    try {
      await chapterApi.updateGenerationProgressApi({
        projectId: projectStore.currentProjectId,
        currentChapter: i + 1,
        completedChapters: genStatus.value.completed,
        failedChapters: genStatus.value.failed,
      })
    } catch { /* ignore */ }
    i++
    next()
  }
  next()
}

function pauseGeneration() {
  chapterPaused.value = true
  chapterProgress.value = '已暂停（点击"继续生成"恢复）'
  chapterApi.pauseGenerationApi(projectStore.currentProjectId).catch(() => {})
}

async function resumeGeneration() {
  chapterPaused.value = false
  await generateAllChapters()
}

async function saveChapterToDb(idx: number) {
  if (!projectStore.currentProjectId) return
  if (!novel.chapters[idx]) return
  const o = novel.outline[idx]
  try {
    await chapterApi.saveChapterApi({
      projectId: projectStore.currentProjectId,
      chapterNumber: idx + 1,
      title: o ? (o.title || ('第' + (idx + 1) + '章')) : ('第' + (idx + 1) + '章'),
      content: novel.chapters[idx],
      status: 'done',
    })
  } catch (e: any) {
    console.error('章节保存失败:', e.message)
  }
}

async function generateOneChapter(idx: number) {
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return false }
  chapterLoading.value = true
  chapterProgress.value = '正在生成第' + (idx + 1) + '章 / 共' + novel.outline.length + '章...'
  const o = novel.outline[idx]
  const prevSummary = idx > 0 ? (novel.chapters[idx - 1] || '').slice(0, 200) : ''
  const prevEnd = idx > 0 ? (novel.chapters[idx - 1] || '').slice(-300) : ''
  let stepContext = ''
  try {
    const summaries = await loadStepSummaries()
    const ctxParts: string[] = []
    if (summaries.world && summaries.world.world) {
      ctxParts.push('[世界观] ' + summaries.world.world.slice(0, 300))
    }
    if (summaries.characters && summaries.characters.characters) {
      ctxParts.push('[角色] ' + summaries.characters.characters.slice(0, 300))
    }
    if (ctxParts.length > 0) stepContext = '\n\n[上下文参考]\n' + ctxParts.join('\n')
  } catch { /* ignore */ }
  try {
    const outlineChapterNum = typeof o.chapter_number === 'string' ? parseInt(o.chapter_number) || (idx + 1) : o.chapter_number
    const d = await novelApi.generateChapterApi({
      endpoint: m.endpoint,
      apiKey: m.apiKey,
      model: m.model,
      projectTitle: novel.title,
      genre: novel.genre,
      chapterNumber: outlineChapterNum || (idx + 1),
      chapterTitle: o.title || '',
      chapterOutline: o.summary + stepContext,
      continuationPoint: prevEnd,
      previousChapterSummary: prevSummary,
      chapterCharacters: (o.characters || []).join(', '),
      targetWordCount: novel.targetWords,
      narrativePerspective: novel.perspective,
      useCraft: novel.useCraft,
    })
    novel.chapters[idx] = d.content
    chapterProgress.value = ''
    await saveChapterToDb(idx)
    return true
  } catch (e: any) {
    chapterProgress.value = '第' + (idx + 1) + '章生成失败: ' + e.message
    return false
  } finally {
    chapterLoading.value = false
  }
}

function exportNovel() {
  if (!novel.chapters.length) { alert('没有可导出的章节'); return }
  let text = novel.title + '\n\n'
  if (novel.description) text += '简介：' + novel.description + '\n\n'
  if (novel.world) text += '=== 世界观 ===\n' + novel.world + '\n\n'
  if (novel.characters) text += '=== 角色 ===\n' + novel.characters + '\n\n'
  text += '=== 正文 ===\n\n'
  novel.chapters.forEach((c, i) => {
    if (!c) return
    const title = novel.outline[i] ? novel.outline[i].title : String(i + 1)
    text += '第' + (i + 1) + '章 ' + title + '\n\n' + c + '\n\n'
  })
  const blob = new Blob(['\uFEFF' + text], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = (novel.title || '小说') + '.txt'
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}

async function runAnalyze() {
  const m = settings.models[analyzeModelIdx.value] || settings.models[0]
  if (!m) { alert('请先选择模型'); return }
  if (!analyzeText.value.trim()) { alert('请先粘贴小说文本'); return }
  analyzeLoading.value = true
  try {
    const d = await novelApi.aiAnalyzeApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: analyzeText.value.trim() })
    analyzeResult.value = d.result
    styleProfile.value = d.result
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  analyzeLoading.value = false
}

async function runGenerate() {
  const m = settings.models[generateModelIdx.value] || settings.models[0]
  if (!m) { alert('请先选择模型'); return }
  if (!styleProfile.value) { alert('请先完成风格分析'); return }
  genLoading.value = true
  try {
    const d = await novelApi.aiGenerateApi({
      endpoint: m.endpoint,
      apiKey: m.apiKey,
      model: m.model,
      styleProfile: styleProfile.value,
      genre: genForm.genre || '未指定',
      count: genForm.count || 3,
      protagonist: genForm.protagonist || '未指定',
      world: genForm.world || '未指定',
      outline: genForm.outline || '未指定',
    })
    genResult.value = d.result
  } catch (e: any) {
    alert('生成失败: ' + e.message)
  }
  genLoading.value = false
}

function saveGenerated() {
  if (!genResult.value) return
  const blob = new Blob(['\uFEFF' + genResult.value], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'AI仿写.txt'
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}

// Modal functions
function openReadChapter(idx: number) {
  readModalIdx.value = idx
  const ch = novel.chapters[idx]
  const title = novel.outline[idx] ? novel.outline[idx].title : ''
  readModalTitle.value = '第' + (idx + 1) + '章 ' + title
  readModalContent.value = ch
  showReadModal.value = true
}

function saveReadModal() {
  novel.chapters[readModalIdx.value] = readModalContent.value
  showReadModal.value = false
}

function openChapterSettings(idx: number) {
  settingsModalIdx.value = idx
  settingsForm.targetWords = novel.targetWords
  settingsForm.extraPrompt = ''
  showSettingsModal.value = true
}

function applyChapterSettings() {
  showSettingsModal.value = false
  const idx = settingsModalIdx.value
  const target = settingsForm.targetWords
  const extra = settingsForm.extraPrompt
  if (idx >= novel.chapters.length) return
  chapterLoading.value = true
  chapterProgress.value = '正在重生成第' + (idx + 1) + '章...'
  const outlineItem = novel.outline[idx]
  const outlineText = novel.outline.map((o: any) => o.title + ' - ' + o.summary).join('\n')
  const prevChapters = novel.chapters.slice(0, idx).map((c, i) => '第' + (i + 1) + '章 ' + novel.outline[i].title + '\n' + c).join('\n\n')
  const prompt = '请根据以下信息重写第' + (idx + 1) + '章《' + (outlineItem ? outlineItem.title : '') + '》\n\n大纲概要：' + (outlineItem ? outlineItem.summary : '') + '\n全书大纲：\n' + outlineText + '\n\n已有章节内容：\n' + prevChapters + '\n\n本章目标字数：' + target + '字' + (extra ? '\n\n特殊要求：' + extra : '') + '\n\n只输出本章正文内容，不要任何解释或前缀'
  const model = getNovelModel()
  apiStream(
    '/api/generate_chapter_stream',
    { model: { name: model.name, endpoint: model.endpoint, apiKey: model.apiKey, model: model.model }, prompt, target_words: target, temperature: 0.7, max_tokens: Math.min(target * 2, 16000) },
    (text) => { novel.chapters[idx] = (novel.chapters[idx] || '') + text },
    () => { chapterLoading.value = false; chapterProgress.value = '重生成完成' },
    (err) => { chapterLoading.value = false; chapterProgress.value = '错误: ' + err }
  )
}

function polishChapter(idx: number) {
  if (idx >= novel.chapters.length) return
  compareIdx.value = idx
  compareOriginal.value = novel.chapters[idx]
  comparePolished.value = ''
  polishLoadingTip.value = '正在润色中，请稍候...'
  showCompareModal.value = true
  const prompt = '请对以下小说章节进行润色优化，保持原意不变，提升文笔流畅度、画面感和节奏感，去除AI痕迹，使语言更自然生动。直接输出润色后的正文内容，不要任何解释。\n\n原文：\n' + novel.chapters[idx]
  const model = getNovelModel()
  apiStream(
    '/api/generate_chapter_stream',
    { model: { name: model.name, endpoint: model.endpoint, apiKey: model.apiKey, model: model.model }, prompt, target_words: 0, temperature: 0.5, max_tokens: 16000 },
    (text) => { comparePolished.value += text },
    () => { polishLoadingTip.value = '润色完成' },
    (err) => { polishLoadingTip.value = '润色失败: ' + err }
  )
}

function openCompare(idx: number) {
  if (idx >= novel.chapters.length) return
  compareIdx.value = idx
  compareOriginal.value = novel.chapters[idx]
  comparePolished.value = '(请点击润色按钮后的结果将显示在这里)'
  polishLoadingTip.value = ''
  showCompareModal.value = true
}

function applyPolish() {
  if (comparePolished.value && comparePolished.value !== '(请点击润色按钮后的结果将显示在这里)') {
    novel.chapters[compareIdx.value] = comparePolished.value
  }
  showCompareModal.value = false
}

async function saveProject() {
  if (!projectStore.projectName.trim()) { alert('请输入项目名称'); return }
  const novelData = JSON.parse(JSON.stringify({
    title: novel.title,
    description: novel.description,
    theme: novel.theme,
    genre: novel.genre,
    world: novel.world,
    characters: novel.characters,
    outlineText: novel.outlineText,
    outline: novel.outline,
    chapters: novel.chapters,
    step: novel.step,
    targetWords: novel.targetWords,
    useCraft: novel.useCraft,
    chapterCount: novel.chapterCount,
    charCount: novel.charCount,
    perspective: novel.perspective,
    styleProfile: novel.styleProfile,
  }))
  try {
    const r = await projectStore.save({
      id: projectStore.currentProjectId || undefined,
      name: projectStore.projectName.trim(),
      step: novel.step || 0,
      novelData,
    })
    projectStore.currentProjectId = r.id
    projectStore.selectedProjectId = r.id
    await projectStore.loadList()
    alert('项目已保存: ' + r.name)
  } catch (e: any) {
    alert('保存失败: ' + e.message)
  }
}

async function loadProject() {
  if (!projectStore.selectedProjectId) return
  try {
    const r = await projectStore.load(projectStore.selectedProjectId)
    if (r.error) { alert(r.error); return }
    projectStore.currentProjectId = r.id
    projectStore.projectName = r.name || ''
    const n = r.data || {}
    Object.assign(novel, {
      title: n.title || '',
      description: n.description || '',
      theme: n.theme || '',
      genre: n.genre || '',
      world: n.world || '',
      characters: n.characters || '',
      outlineText: n.outlineText || '',
      outline: n.outline || [],
      chapters: n.chapters || [],
      step: n.step || 0,
      targetWords: n.targetWords || 3000,
      useCraft: n.useCraft || false,
      chapterCount: n.chapterCount || 10,
      charCount: n.charCount || 3,
      perspective: n.perspective || '第三人称',
      styleProfile: n.styleProfile || '',
    })
    await loadOutlinesFromDb()
    await loadChaptersFromDb()
    alert('已加载项目: ' + r.name)
  } catch (e: any) {
    alert('加载失败: ' + e.message)
  }
}

async function deleteProject() {
  if (!projectStore.selectedProjectId) return
  const proj = projectStore.projectList.find(p => p.id === projectStore.selectedProjectId)
  if (!proj) return
  if (!confirm('确定删除项目 "' + proj.name + '"？')) return
  try {
    await projectStore.remove(projectStore.selectedProjectId)
    alert('已删除')
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

function newProject() {
  Object.assign(novel, {
    title: '', description: '', theme: '', genre: '',
    world: '', characters: '', outlineText: '', outline: [],
    chapters: [], step: 0, targetWords: 3000, useCraft: false,
    chapterCount: 10, charCount: 3, perspective: '第三人称', styleProfile: '',
  })
  projectStore.projectName = ''
  projectStore.selectedProjectId = ''
}

onMounted(() => {
  projectStore.loadList()
})
</script>
