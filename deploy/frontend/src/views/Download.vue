<template>
  <div>
    <div class="card">
      <h2>搜索书籍</h2>
      <div class="search-box">
        <input
          type="text"
          v-model="store.searchQuery"
          placeholder="书名 / 章节链接 / book_id"
          @keydown.enter="store.search()"
        />
        <button @click="store.search()" :disabled="store.searchLoading">
          <span v-if="store.searchLoading" class="spinner"></span>搜索
        </button>
      </div>
      <div class="tip">输入书名、粘贴链接或直接输入 book_id</div>
      <div
        v-for="r in store.searchResults"
        :key="r.book_id"
        class="book-item"
        :class="{ selected: store.selectedBook && store.selectedBook.book_id === r.book_id }"
        @click="store.selectBook(r)"
      >
        <div>
          <div class="book-title">{{ r.title || r.book_name || '未知书名' }}</div>
          <div class="book-meta">{{ r.author || '' }}</div>
        </div>
        <div class="book-count">{{ store.bookCounts[r.book_id] || '...' }}</div>
      </div>
      <div v-if="store.searchError" class="error">{{ store.searchError }}</div>
    </div>

    <div class="card" v-if="store.selectedBook">
      <h2>{{ store.selectedBook.title || store.selectedBook.book_id }}</h2>
      <div style="font-size:11px;color:#888;margin-bottom:10px">
        {{ store.selectedBook.author ? store.selectedBook.author + ' | ' : '' }}{{ store.selectedBook.count }}{{ store.selectedBook.count ? ' 章' : '' }}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">
        <button class="btn btn-dl" @click="store.startDownload()" :disabled="store.dlState === 'running'">
          {{ store.dlState === 'done' ? '重新下载' : '下载 TXT' }}
        </button>
        <button class="btn btn-ghost" @click="store.resetSearch()">重新搜索</button>
      </div>
      <div v-if="store.dlState !== 'idle'">
        <div class="progress">
          <div class="progress-top">
            <span class="progress-label">{{ statusText }}</span>
            <span class="progress-pct">{{ percentage }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: percentage + '%' }"></div>
          </div>
          <div class="progress-detail">
            <span>{{ store.dlCurrent }}/{{ store.dlTotal }} 章</span>
          </div>
        </div>
        <div style="margin-top:6px" v-if="store.dlState === 'running'">
          <button class="btn btn-pause" @click="store.pauseDownload()">暂停</button>
        </div>
        <div style="margin-top:6px" v-if="store.dlState === 'paused'">
          <button class="btn btn-resume" @click="store.resumeDownload()">继续</button>
          <button class="btn btn-save" @click="store.saveFile()">保存</button>
        </div>
        <div style="margin-top:6px" v-if="store.dlState === 'done'">
          <div class="success">
            下载完成!
            <button class="btn btn-dl" @click="store.saveFile()" style="margin-left:5px">保存文件</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDownloadStore } from '../stores/download'

const store = useDownloadStore()

const percentage = computed(() =>
  store.dlTotal > 0 ? Math.round(store.dlCurrent / store.dlTotal * 100) : 0
)

const statusText = computed(() => {
  if (store.dlState === 'running') return '下载中 ' + percentage.value + '%'
  if (store.dlState === 'paused') return '已暂停 ' + percentage.value + '%'
  if (store.dlState === 'done') return '下载完成!'
  if (store.dlState === 'error') return '下载失败'
  return '点击下方按钮开始'
})
</script>
