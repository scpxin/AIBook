<template>
  <Modal :title="'章节参数设置 - 第' + (modals.settingsIdx + 1) + '章'" @close="modals.showSettings = false" v-if="modals.showSettings">
    <div class="form-group"><label>目标字数</label><input v-model.number="modals.settingsTargetWords" type="number" min="500" max="20000" step="500" /></div>
    <div class="form-group"><label>额外提示词（可选）</label><input v-model="modals.settingsExtraPrompt" placeholder="如：增加打斗描写、突出主角智慧" /></div>
    <div style="display:flex;gap:8px;margin-top:10px">
      <button class="btn btn-ai" style="flex:1" @click="onApply">应用并重生成</button>
      <button class="btn" style="flex:1;background:#ccc;color:#333" @click="modals.showSettings = false">取消</button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Modal from '../Modal.vue'
import { useModalsStore } from '../../stores/modals'

const modals = useModalsStore()

const emit = defineEmits<{ apply: [idx: number, target: number, extra: string] }>()

function onApply() {
  emit('apply', modals.settingsIdx, modals.settingsTargetWords, modals.settingsExtraPrompt)
}
</script>
