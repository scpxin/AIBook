<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div v-if="visible" class="dialog-overlay" @click.self="onCancel">
        <div class="dialog-box" role="dialog" aria-modal="true" aria-labelledby="dlg-title" aria-describedby="dlg-msg">
          <div class="dialog-header">
            <h3 id="dlg-title">{{ options.title }}</h3>
          </div>
          <div class="dialog-body">
            <p id="dlg-msg" class="dialog-message">{{ options.message }}</p>
            <p v-if="options.detail" class="dialog-detail">{{ options.detail }}</p>
          </div>
          <div class="dialog-footer">
            <button @click="onCancel" class="btn-cancel">{{ options.cancelText }}</button>
            <button @click="onConfirm" :class="['btn-confirm', typeClass]">{{ options.confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { setupConfirm } from '../composables/useConfirm'

const { visible, options, handleConfirm, handleCancel } = setupConfirm()

const typeClass = computed(() => {
  if (options.value.type === 'danger') return 'btn-danger'
  if (options.value.type === 'info') return 'btn-info'
  return ''
})

function onConfirm() { handleConfirm() }
function onCancel() { handleCancel() }
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
}
.dialog-box {
  background: #fff; border-radius: 12px; padding: 24px 28px;
  min-width: 320px; max-width: 480px; width: 90vw;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
}
.dialog-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #1a1a1a; }
.dialog-body { margin: 12px 0 20px; }
.dialog-message { margin: 0; font-size: 14px; color: #333; line-height: 1.6; }
.dialog-detail { margin: 8px 0 0; font-size: 12px; color: #888; line-height: 1.5; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel {
  padding: 8px 20px; border: 1px solid #d9d9d9; background: #fff;
  border-radius: 6px; font-size: 14px; cursor: pointer; color: #555;
}
.btn-cancel:hover { border-color: #409eff; color: #409eff; }
.btn-confirm {
  padding: 8px 20px; border: none; background: #409eff; color: #fff;
  border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-confirm:hover { background: #66b1ff; }
.btn-danger { background: #f56c6c; }
.btn-danger:hover { background: #f89898; }
.btn-info { background: #909399; }
.btn-info:hover { background: #a6a9ad; }

.dialog-fade-enter-active, .dialog-fade-leave-active { transition: opacity 0.2s; }
.dialog-fade-enter-from, .dialog-fade-leave-to { opacity: 0; }
.dialog-fade-enter-active .dialog-box { transition: transform 0.2s; }
.dialog-fade-enter-from .dialog-box { transform: scale(0.95); }
</style>
