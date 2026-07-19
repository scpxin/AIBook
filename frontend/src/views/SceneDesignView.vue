<template>
  <div v-if="pageLoading" class="page-loading">
    <div class="loading-spinner"></div>
    <p>加载中...</p>
  </div>
  <div v-else class="scene-design-view">
    <div class="section">
      <h3>场景设计</h3>
      <p class="tip">为每个章节设计具体场景：环境氛围、出场人物、关键事件</p>

      <div class="form-group">
        <label>章节选择</label>
        <select v-model="form.chapterNo" class="form-select">
          <option v-for="i in 10" :key="i" :value="i">第 {{ i }} 章</option>
        </select>
      </div>

      <div class="form-group">
        <label>场景名称</label>
        <input v-model="form.sceneName" placeholder="如：山门拜师、密林遇袭..." class="form-input" />
      </div>

      <div class="form-group">
        <label>场景氛围</label>
        <select v-model="form.atmosphere" class="form-select">
          <option value="tense">紧张刺激</option>
          <option value="calm">平和日常</option>
          <option value="mysterious">神秘诡异</option>
          <option value="epic">史诗恢弘</option>
          <option value="emotional">情感浓烈</option>
          <option value="humorous">轻松诙谐</option>
        </select>
      </div>

      <div class="form-group">
        <label>出场人物</label>
        <input v-model="form.characters" placeholder="如：主角、师兄李青、长老王玄..." class="form-input" />
      </div>

      <div class="form-group">
        <label>关键事件概要</label>
        <textarea v-model="form.event" rows="4" placeholder="描述本场景发生的核心事件..." class="form-textarea"></textarea>
      </div>

      <div class="form-group">
        <label>场景钩子（悬念）</label>
        <input v-model="form.hook" placeholder="本场景结尾留下的悬念..." class="form-input" />
      </div>

      <div class="action-row">
        <button @click="generateAI" :disabled="loading" class="btn btn-primary">
          <span v-if="loading" class="spinner"></span>{{ loading ? '生成中...' : 'AI生成场景' }}
        </button>
        <button @click="addScene" class="btn btn-ghost">+ 手动添加场景</button>
        <button @click="save" :disabled="loading" class="btn btn-ghost">保存场景设计</button>
        <button @click="save" :disabled="loading" class="btn btn-ghost">完成</button>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="scenes.length" class="section">
      <h3>场景列表（{{ scenes.length }}个）</h3>
      <div v-for="(scene, idx) in scenes" :key="idx" class="scene-card" tabindex="0" v-keyboard-click>
        <div v-if="editingIdx !== idx">
          <div class="scene-header">
            <span class="scene-ch">第{{ scene.chapterNo }}章</span>
            <span class="scene-name">{{ scene.sceneName }}</span>
            <span class="scene-atmo">{{ atmoText(scene.atmosphere) }}</span>
            <span class="scene-actions">
              <button @click="startEdit(idx)" class="btn btn-sm btn-ghost">编辑</button>
              <button @click="deleteScene(idx)" class="btn btn-sm btn-danger">删除</button>
            </span>
          </div>
          <div class="scene-event">{{ scene.event }}</div>
          <div class="scene-hook">悬念：{{ scene.hook }}</div>
        </div>
        <div v-else class="scene-edit-form">
          <div class="form-group">
            <label>场景名称</label>
            <input v-model="editForm.sceneName" class="form-input" />
          </div>
          <div class="form-group">
            <label>氛围</label>
            <select v-model="editForm.atmosphere" class="form-select">
              <option value="tense">紧张刺激</option>
              <option value="calm">平和日常</option>
              <option value="mysterious">神秘诡异</option>
              <option value="epic">史诗恢弘</option>
              <option value="emotional">情感浓烈</option>
              <option value="humorous">轻松诙谐</option>
            </select>
          </div>
          <div class="form-group">
            <label>出场人物</label>
            <input v-model="editForm.characters" class="form-input" />
          </div>
          <div class="form-group">
            <label>关键事件</label>
            <textarea v-model="editForm.event" rows="3" class="form-textarea"></textarea>
          </div>
          <div class="form-group">
            <label>悬念钩子</label>
            <input v-model="editForm.hook" class="form-input" />
          </div>
          <div class="action-row">
            <button @click="saveEdit(idx)" class="btn btn-primary btn-sm">保存</button>
            <button @click="cancelEdit" class="btn btn-ghost btn-sm">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { saveModuleData, getModuleData, getAllModuleData, designScenes } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'
import { vKeyboardClick } from '../directives/keyboardClick'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('scene_design', '场景设计')
const confirm = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()
const pageLoading = ref(true)

const form = reactive({
  chapterNo: 1,
  sceneName: '',
  atmosphere: 'tense',
  characters: '',
  event: '',
  hook: '',
})
const loading = ref(false)
const error = ref('')
const scenes = ref<any[]>([])
const chapterOutlines = ref<any>(null)
const editingIdx = ref<number | null>(null)
const editForm = reactive({
  sceneName: '',
  atmosphere: 'tense',
  characters: '',
  event: '',
  hook: '',
  chapterNo: 1,
})

async function generateAI() {
  loading.value = true
  gen.begin()
  error.value = ''
  try {
    const result = await designScenes(props.projectId, chapterOutlines.value || {})
    if (result?.scenes?.length) {
      scenes.value = result.scenes.map((s: any) => ({
        chapterNo: form.chapterNo,
        sceneName: s.name || s.title || '',
        atmosphere: s.atmosphere || form.atmosphere,
        characters: (s.characters || []).join(', '),
        event: s.event || s.summary || '',
        hook: s.hook || '',
      }))
    } else {
      error.value = 'AI未返回场景数据'
    }
  } catch (e: any) {
    errorBar.showError(e, () => generateAI())
  } finally {
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

function atmoText(a: string): string {
  const map: Record<string, string> = { tense: '紧张', calm: '平和', mysterious: '神秘', epic: '史诗', emotional: '情感', humor: '轻松' }
  return map[a] || a
}

function addScene() {
  if (!form.sceneName || !form.event) {
    error.value = '请填写场景名称和关键事件'
    return
  }
  scenes.value.push({ ...form })
  form.sceneName = ''
  form.event = ''
  form.hook = ''
  form.characters = ''
  error.value = ''
}

function startEdit(idx: number) {
  const s = scenes.value[idx]
  editingIdx.value = idx
  editForm.sceneName = s.sceneName || ''
  editForm.atmosphere = s.atmosphere || 'tense'
  editForm.characters = s.characters || ''
  editForm.event = s.event || ''
  editForm.hook = s.hook || ''
  editForm.chapterNo = s.chapterNo || 1
}

function saveEdit(idx: number) {
  if (!editForm.sceneName || !editForm.event) {
    error.value = '请填写场景名称和关键事件'
    return
  }
  scenes.value[idx] = { ...editForm }
  editingIdx.value = null
  error.value = ''
}

function cancelEdit() {
  editingIdx.value = null
}

async function deleteScene(idx: number) {
  const ok = await confirm.confirm({
    message: '确定删除该场景？',
    detail: '删除后不可恢复，请确认',
    type: 'danger',
  })
  if (!ok) return
  scenes.value.splice(idx, 1)
  if (editingIdx.value === idx) editingIdx.value = null
}

async function save() {
  const ok = await confirm.confirm({
    message: '确定完成场景设计？',
    detail: '确认后将保存当前场景数据并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  loading.value = true
  gen.begin()
  error.value = ''
  try {
    await saveModuleData(props.projectId, 'scene_design', { scenes: scenes.value })
    emit('complete', { scenes: scenes.value })
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

onMounted(async () => {
  try {
    try {
      const saved = await getModuleData(props.projectId, 'scene_design')
      if (saved?.data) {
        const d = saved.data
        scenes.value = Array.isArray(d) ? d : (d.scenes || [])
      }
    } catch (_e) { /* ignore */ }
    try {
      const allData = await getAllModuleData(props.projectId)
      chapterOutlines.value = allData?.modules?.['chapter_outline'] || null
      const characters = allData?.modules?.['characters']
      if (characters && Array.isArray(characters) && characters.length > 0) {
        form.characters = characters.map((c: any) => c.name || c.char_id).filter(Boolean).join(', ')
      }
    } catch (_e) { /* ignore */ }
  } finally {
    pageLoading.value = false
  }
})

const sceneData = () => ({ scenes: scenes.value })
const { saveState, scheduleSave } = useAutoSave({
  dataRef: sceneData,
  saveFn: async (data) => {
    await saveModuleData(props.projectId, 'scene_design', data)
  },
  debounce: 2000,
  storageKey: `scenes_${props.projectId}`,
  onSaveError: () => toast.error('场景设计自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'scene_design',
})
watch(scenes, () => {
  scheduleSave()
}, { deep: true })
</script>

<style scoped>
.scene-design-view { max-width: 900px; }
.section { background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.section h3 { font-size: 22px; margin-bottom: 10px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 16px; color: #555; }
.form-input, .form-select, .form-textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; resize: vertical; font-family: inherit; }
.form-textarea { min-height: 90px; }
.action-row { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.error { color: #e74c3c; margin-top: 12px; font-size: 15px; }
.scene-card { border: 1px solid #eee; border-radius: 12px; padding: 18px; margin-bottom: 14px; background: #fafafa; }
.scene-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.scene-ch { background: var(--primary); color: #fff; padding: 3px 10px; border-radius: 6px; font-size: 14px; font-weight: 600; }
.scene-name { font-weight: 700; font-size: 17px; flex: 1; }
.scene-atmo { background: #e8f8f0; color: #27ae60; padding: 3px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; }
.scene-event { color: #555; font-size: 15px; line-height: 1.6; margin-bottom: 8px; }
.scene-hook { font-size: 14px; color: #e67e22; background: #fef3e2; padding: 8px 12px; border-radius: 8px; }
.scene-actions { display: flex; gap: 6px; }
.btn-sm { padding: 6px 12px; font-size: 13px; }
.btn-danger { background: #fff3f3; color: #c62828; }
.scene-edit-form { background: #f8f9fa; border-radius: 10px; padding: 18px; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
