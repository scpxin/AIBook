<template>
  <Modal title="AI 润色" :card-style="{ maxWidth: '1200px', width: '95vw' }" @close="modals.showPolish = false" v-if="modals.showPolish">
    <h3>AI 润色 - 第{{ modals.polishIdx + 1 }}章</h3>
    <div style="display:flex;height:100%;gap:8px;margin-top:8px">
      <textarea v-model="modals.polishOriginal" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit"></textarea>
      <textarea v-model="modals.polishResult" class="chapter-detail" style="flex:1;min-height:400px;padding:8px;font-size:12px;line-height:1.7;resize:none;font-family:inherit" readonly></textarea>
    </div>
    <div style="font-size:11px;color:#666;margin-top:4px">{{ modals.polishTip }}</div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn" style="flex:1;background:#11998e;color:#fff" @click="modals.savePolish()">采用润色版</button>
      <button class="btn" style="flex:1;background:#ccc;color:#333" @click="modals.showPolish = false">取消</button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Modal from '../Modal.vue'
import { useModalsStore } from '../../stores/modals'

const modals = useModalsStore()
</script>
