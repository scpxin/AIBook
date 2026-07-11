<template>
  <div class="scene-design-view">
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
        <button @click="$emit('complete', { scenes })" class="btn btn-ghost">完成</button>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="scenes.length" class="section">
      <h3>场景列表（{{ scenes.length }}个）</h3>
      <div v-for="(scene, idx) in scenes" :key="idx" class="scene-card">
        <div class="scene-header">
          <span class="scene-ch">第{{ scene.chapterNo }}章</span>
          <span class="scene-name">{{ scene.sceneName }}</span>
          <span class="scene-atmo">{{ atmoText(scene.atmosphere) }}</span>
        </div>
        <div class="scene-event">{{ scene.event }}</div>
        <div class="scene-hook">悬念：{{ scene.hook }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { saveModuleData, getModuleData, getAllModuleData, designScenes } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('scene_design', '场景设计')

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
    error.value = e.message || 'AI场景生成失败，可手动添加'
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

async function save() {
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
})
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
</style>
