<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div v-for="toast in toastStore.toasts" :key="toast.id" :class="['toast', `toast-${toast.type}`]" @click="toastStore.dismiss(toast.id)">
        <span class="toast-icon">{{ icons[toast.type] }}</span>
        <span class="toast-msg">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from '../stores/toast'

const toastStore = useToastStore()
const icons: Record<string, string> = { success: '✓', error: '✕', info: 'ℹ' }
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
.toast-icon { font-size: 16px; font-weight: 700; }
.toast-msg { flex: 1; }
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
