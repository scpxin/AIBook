<template>
  <Modal title="查看章节" :card-style="{ maxWidth: '1000px', width: '90vw' }" @close="modals.showRead = false" v-if="modals.showRead">
    <h3>{{ modals.readTitle }}</h3>
    <textarea v-model="modals.readContent" class="chapter-detail" style="width:100%;min-height:500px;padding:12px;font-size:14px;line-height:1.8;font-family:inherit;resize:vertical;box-sizing:border-box"></textarea>
    <div style="display:flex;gap:8px;margin-top:10px">
      <button class="btn btn-ai" style="flex:1" @click="modals.saveRead()">保存修改</button>
      <button class="btn" style="flex:1;background:#ccc;color:#333" @click="modals.showRead = false">关闭</button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Modal from '../Modal.vue'
import { useModalsStore } from '../../stores/modals'

const modals = useModalsStore()
</script>
