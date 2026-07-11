<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-card" :style="cardStyle as any">
        <button class="modal-close" @click="$emit('close')">&times;</button>
        <h3 v-if="title">{{ title }}</h3>
        <slot />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  cardStyle?: string | Record<string, string>
}>()

defineEmits<{ close: [] }>()
</script>
