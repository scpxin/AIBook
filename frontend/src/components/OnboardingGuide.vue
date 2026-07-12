<template>
  <Teleport to="body">
    <div v-if="modelValue" class="onboarding-overlay" @click.self="close">
      <div class="onboarding-card">
        <button class="close-btn" @click="close" aria-label="关闭">×</button>
        <div class="step-indicator">
          <span
            v-for="(_, idx) in steps"
            :key="idx"
            class="step-dot"
            :class="{ active: idx === currentStep, done: idx < currentStep }"
          />
        </div>
        <h2 class="step-title">{{ steps[currentStep].title }}</h2>
        <p class="step-content">{{ steps[currentStep].content }}</p>
        <div v-if="steps[currentStep].tip" class="step-tip">
          {{ steps[currentStep].tip }}
        </div>
        <div class="nav-buttons">
          <button
            v-if="currentStep > 0"
            class="btn-prev"
            @click="currentStep--"
          >
            上一步
          </button>
          <button
            class="btn-next"
            @click="handleNext"
          >
            {{ currentStep < steps.length - 1 ? '下一步' : '开始使用' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const currentStep = ref(0)

const steps = [
  {
    title: '欢迎来到 AI 小说创作平台',
    content: '这是一个全流程AI创作工具，从创意构思到成稿输出，19个模块一站式完成小说创作。',
    tip: '全流程无需离开页面，逐步推进即可。',
  },
  {
    title: '先配置大模型API',
    content: '点击右上角「设置」按钮，配置你的大模型API（支持OpenAI、Claude、国产模型等）。没有API也能体验基础流程。',
    tip: '配置后可解锁AI生成、续写、一致性检查等功能。',
  },
  {
    title: '创作流程说明',
    content: '系统包含：创意→项目规划→世界观→角色→力量体系→势力→剧情设计→场景设计→草稿→正文等模块。完成一个模块后点击「下一步」继续。',
    tip: '每个模块都有AI生成按钮，也可以手动编辑后保存。',
  },
  {
    title: '数据安全',
    content: '所有数据自动保存到服务器，关闭浏览器也不丢失。草稿每15秒自动保存，异常退出时从本地备份恢复。',
    tip: '导出功能支持TXT/Markdown/DOCX格式。',
  },
]

function handleNext() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  } else {
    close()
  }
}

function close() {
  emit('update:modelValue', false)
  currentStep.value = 0
}
</script>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.onboarding-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  max-width: 480px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  text-align: center;
}
.close-btn {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
}
.close-btn:hover { color: #333; }
.step-indicator {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 24px;
}
.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ddd;
  transition: all 0.3s;
}
.step-dot.active { background: var(--primary); transform: scale(1.3); }
.step-dot.done { background: #52c41a; }
.step-title { font-size: 22px; margin: 0 0 12px; color: #333; }
.step-content { font-size: 16px; color: #555; line-height: 1.6; margin: 0 0 12px; }
.step-tip {
  font-size: 13px;
  color: #888;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 24px;
}
.nav-buttons { display: flex; gap: 12px; justify-content: center; }
.btn-prev {
  padding: 10px 24px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
}
.btn-next {
  padding: 10px 24px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
}
.btn-next:hover { opacity: 0.9; }
</style>
