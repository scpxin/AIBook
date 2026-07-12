<template>
  <Transition name="error-slide">
    <div v-if="state.show" :class="['error-bar', `error-${state.type}`]" role="alert">
      <span class="error-icon">
        <svg v-if="state.type === 'error'" width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 4.5v5M8 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <svg v-else-if="state.type === 'warning'" width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 1.5L15 14H1L8 1.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6v4M8 12v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 7v4M8 5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </span>
      <span class="error-text">{{ state.message }}</span>
      <button v-if="state.retry" @click="handleRetry" class="btn-retry">重试</button>
      <button @click="dismiss" class="btn-close" aria-label="关闭">&times;</button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { setupErrorBar } from '../composables/useErrorBar'

const { state, dismiss } = setupErrorBar()

async function handleRetry() {
  dismiss()
  await state.value.retry?.()
}
</script>

<style scoped>
.error-bar {
  position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 9999; display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  max-width: 90vw; font-size: 13px; line-height: 1.4;
}
.error-error { background: #fef0f0; border: 1px solid #fde2e2; color: #c45656; }
.error-warning { background: #fdf6ec; border: 1px solid #faecd8; color: #b88230; }
.error-info { background: #f4f4f5; border: 1px solid #e9e9eb; color: #73767a; }
.error-icon { flex-shrink: 0; display: flex; align-items: center; }
.error-text { flex: 1; word-break: break-word; }
.btn-retry {
  padding: 3px 10px; border: 1px solid currentColor; background: transparent;
  border-radius: 4px; font-size: 12px; cursor: pointer; color: inherit; opacity: 0.8;
}
.btn-retry:hover { opacity: 1; }
.btn-close {
  background: none; border: none; font-size: 18px; cursor: pointer;
  color: inherit; opacity: 0.5; padding: 0 4px; line-height: 1;
}
.btn-close:hover { opacity: 1; }

.error-slide-enter-active, .error-slide-leave-active { transition: all 0.3s; }
.error-slide-enter-from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
.error-slide-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }
</style>
