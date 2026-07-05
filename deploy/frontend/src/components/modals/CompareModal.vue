<template>
  <Modal title="对比" :card-style="{ maxWidth: '1200px', width: '95vw' }" @close="modals.showCompare = false" v-if="modals.showCompare">
    <h3>章节内容 - 第{{ modals.compareIdx + 1 }}章</h3>
    <div style="display:flex;height:100%;gap:8px;margin-top:8px">
      <textarea v-model="modals.compareOriginal" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit"></textarea>
      <textarea :value="placeholder" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit" readonly></textarea>
    </div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn" style="flex:1;background:#ccc;color:#333" @click="modals.showCompare = false">关闭</button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Modal from '../Modal.vue'
import { useModalsStore } from '../../stores/modals'

const modals = useModalsStore()
const placeholder = '(润色后内容将显示在这里)'
</script>
