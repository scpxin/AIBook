<template>
  <div class="streaming-output" ref="outputRef">
    <div v-if="!content && !streaming" class="placeholder">{{ placeholder }}</div>
    <div v-else class="content" v-html="renderedContent"></div>
    <span v-if="streaming" class="cursor">&#9646;</span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps<{
  content: string
  streaming?: boolean
  placeholder?: string
}>()

const outputRef = ref<HTMLElement | null>(null)

const renderedContent = computed(() => {
  if (!props.content) return ''
  return props.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

watch(() => props.content, async () => {
  await nextTick()
  if (outputRef.value) {
    outputRef.value.scrollTop = outputRef.value.scrollHeight
  }
})
</script>

<style scoped>
.streaming-output {
  flex: 1;
  padding: 21px 20px;
  overflow-y: auto;
  font-size: 18px;
  line-height: 1.8;
  position: relative;
  background: #fff;
}
.placeholder { color: #bbb; font-style: italic; }
.content { white-space: normal; color: #333; }
.cursor { display: inline-block; width: 10px; background: var(--primary); animation: blink 0.8s infinite; vertical-align: text-bottom; margin-left: 3px; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
</style>
