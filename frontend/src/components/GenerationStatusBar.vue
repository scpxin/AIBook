<template>
  <Transition name="gen-bar">
    <div v-if="generation.isGenerating" class="gen-status-bar">
      <div class="gen-pulse"></div>
      <div class="gen-info">
        <span class="gen-label">{{ generation.state?.message || '正在生成...' }}</span>
        <span v-if="totalSteps > 1" class="gen-step">{{ generation.state?.currentStep || 0 }}/{{ totalSteps }}</span>
      </div>
      <div class="gen-elapsed">{{ formattedElapsed }}</div>
      <button class="gen-cancel-btn" @click="generation.cancelGeneration()" title="取消生成">✕ 取消</button>
      <button class="gen-skip-btn" @click="$emit('skip')" title="跳过当前步骤">跳过</button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGenerationStore } from '../stores/generation'

const emit = defineEmits(['skip'])
const generation = useGenerationStore()

const totalSteps = computed(() => generation.state?.totalSteps || 1)

const formattedElapsed = computed(() => {
  const s = generation.elapsed
  if (s < 60) return `${s}秒`
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}分${sec}秒`
})
</script>

<style scoped>
.gen-status-bar {
  position: relative;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
    padding: 10px 24px;
    background: linear-gradient(135deg, #1a73e8, #4285f4);
    color: #fff;
    font-size: 14px;
    box-shadow: 0 2px 12px rgba(26, 115, 232, 0.4);
    border-radius: 8px;
    margin-bottom: 8px;
  }
.gen-pulse {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  animation: gen-pulse 1.2s ease-in-out infinite;
}
@keyframes gen-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}
.gen-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}
.gen-label {
  font-weight: 500;
}
.gen-step {
  font-size: 12px;
  background: rgba(255,255,255,0.2);
  padding: 2px 8px;
  border-radius: 10px;
}
.gen-elapsed {
  font-size: 12px;
  opacity: 0.85;
  font-variant-numeric: tabular-nums;
  min-width: 50px;
  text-align: right;
}
.gen-cancel-btn, .gen-skip-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.gen-cancel-btn:hover, .gen-skip-btn:hover { background: rgba(255, 255, 255, 0.3); }
.gen-skip-btn { margin-left: 4px; }
.gen-bar-enter-active { animation: gen-slide-down 0.3s ease-out; }
.gen-bar-leave-active { animation: gen-slide-up 0.3s ease-in; }
@keyframes gen-slide-down {
  from { transform: translateY(-100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@keyframes gen-slide-up {
  from { transform: translateY(0); opacity: 1; }
  to { transform: translateY(-100%); opacity: 0; }
}
</style>
