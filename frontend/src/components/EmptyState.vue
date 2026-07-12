<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <slot name="icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 21V9" />
        </svg>
      </slot>
    </div>
    <h4 class="empty-state-title">{{ title }}</h4>
    <p v-if="description" class="empty-state-desc">{{ description }}</p>
    <div class="empty-state-action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: var(--text-muted, #888);
}

.empty-state-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary, #aaa);
}

.empty-state-desc {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.5;
}

.empty-state-action {
  margin-top: 8px;
}
</style>
