<template>
  <div>
    <div v-for="b in books" :key="b.book_id" class="book-item" :class="{ selected: modelValue === b.book_id }" @click="$emit('select', b)">
      <div>
        <div class="book-title">{{ b.title }}</div>
        <div class="book-meta">{{ b.book_id }} | {{ b.total || 0 }} 章 | {{ Math.round(b.size / 1024) }}KB</div>
      </div>
      <button v-if="showAction" class="btn btn-ai" style="padding:4px 12px;font-size:11px" :disabled="loading && modelValue === b.book_id">
        {{ loading && modelValue === b.book_id ? '分析中...' : actionText }}
      </button>
    </div>
    <div v-if="!books.length" class="empty">暂无已下载书籍</div>
  </div>
</template>

<script setup lang="ts">
import type { SavedBook } from '../api/client'

defineProps<{
  books: SavedBook[]
  modelValue?: string
  showAction?: boolean
  loading?: boolean
  actionText?: string
}>()

defineEmits<{ select: [book: SavedBook] }>()
</script>
