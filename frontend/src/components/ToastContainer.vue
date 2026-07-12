<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div v-for="toast in toastStore.toasts" :key="toast.id" :class="['toast', `toast-${toast.type}`]">
        <span class="toast-icon">{{ icons[toast.type] || '•' }}</span>
        <span class="toast-msg">{{ toast.message }}</span>
        <button v-if="toast.action" class="toast-action-btn" @click.stop="toast.action!.handler(); toastStore.dismiss(toast.id)">{{ toast.action.label }}</button>
        <button class="toast-close" @click.stop="toastStore.dismiss(toast.id)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from '../stores/toast'

const toastStore = useToastStore()
const icons: Record<string, string> = { success: '✓', error: '✕', info: 'ℹ', action: '💡' }
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  min-width: 200px;
  max-width: 400px;
}
.toast-success { background: #52c41a; }
.toast-error { background: #ff4d4f; }
.toast-info { background: #1890ff; }
.toast-action { background: #fa8c16; }
.toast-icon { font-size: 16px; font-weight: 700; }
.toast-msg { flex: 1; }
.toast-action-btn {
  background: rgba(255,255,255,0.25);
  border: 1px solid rgba(255,255,255,0.5);
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.toast-action-btn:hover { background: rgba(255,255,255,0.4); }
.toast-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0.7;
}
.toast-close:hover { opacity: 1; }
.toast-enter-active { animation: toast-in 0.3s ease-out; }
.toast-leave-active { animation: toast-out 0.3s ease-in; }
@keyframes toast-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes toast-out {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}
</style>
