<template>
  <div class="novel-steps">
    <div v-for="(label, i) in labels" :key="i" class="novel-step" :class="{ active: modelValue === i, done: hasContent(i) }" @click="$emit('change', i)">{{ label }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  labels: string[]
  modelValue: number
  hasContent: (index: number) => boolean
}>()

defineEmits<{ change: [index: number] }>()
</script>
