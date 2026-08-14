import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SavedBook } from '../api/client'
import * as downloadApi from '../api/download'
import { useToastStore } from './toast'

export interface DownloadSession {
  sessionId: string
  bookId: string
  title: string
  status: string
  current: number
  total: number
}

export interface BookSearchItem {
  bookId: string
  bookName?: string
  title?: string
  author?: string
}

export interface SelectedBookInfo {
  bookId: string
  title?: string
  author?: string
  count?: string | number
}

export const useDownloadStore = defineStore('download', () => {
  const searchQuery = ref('')
  const searchLoading = ref(false)
  const searchResults = ref<BookSearchItem[]>([])
  const searchError = ref('')
  const bookCounts = ref<Record<string, string>>({})
  const selectedBook = ref<SelectedBookInfo | null>(null)
  const dlState = ref('idle')
  const dlCurrent = ref(0)
  const dlTotal = ref(0)
  const dlSessionId = ref<string | null>(null)
  const savedBooks = ref<SavedBook[]>([])

  async function search() {
    if (!searchQuery.value.trim()) return
    searchLoading.value = true
    searchError.value = ''
    searchResults.value = []
    selectedBook.value = null
    bookCounts.value = {}

    try {
      const idMatch = searchQuery.value.match(/(\d{16,20})/)
      if (idMatch) {
        const info = await downloadApi.resolveBook(searchQuery.value)
        if (info && info.bookId) {
          selectedBook.value = info
          searchLoading.value = false
          return
        }
      }
      const data = await downloadApi.searchBooks(searchQuery.value)
      searchResults.value = data.books || []
      searchResults.value.forEach(b => {
        downloadApi.directoryApi(b.bookId).then(d => {
          bookCounts.value[b.bookId] = d.total + ' 章'
        }).catch(() => {})
      })
    } catch (e: unknown) {
      searchError.value = e instanceof Error ? e.message : String(e)
    }
    searchLoading.value = false
  }

  function selectBook(b: { bookId: string; bookName?: string; title?: string; author?: string }) {
    selectedBook.value = {
      bookId: b.bookId,
      title: b.title || b.bookName,
      author: b.author,
      count: bookCounts.value[b.bookId],
    }
    dlState.value = 'idle'
    dlCurrent.value = 0
    dlTotal.value = 0
  }

  function resetSearch() {
    selectedBook.value = null
    searchResults.value = []
    searchQuery.value = ''
    dlState.value = 'idle'
  }

  async function startDownload() {
    if (!selectedBook.value || dlState.value === 'running') return
    if (dlState.value === 'paused' && dlSessionId.value) {
      await resumeDownload()
      return
    }
    cancelPoll()
    dlState.value = 'running'
    dlCurrent.value = 0
    try {
      const d = await downloadApi.downloadStart(selectedBook.value.bookId, selectedBook.value.title || '')
      dlSessionId.value = d.sessionId
      pollDownload()
    } catch (e: unknown) {
      dlState.value = 'idle'
      useToastStore().error('启动下载失败: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  let _pollRetryCount = 0
  const MAX_POLL_RETRIES = 5
  let _pollTimer: ReturnType<typeof setTimeout> | null = null
  let _pollActive = false

  function pollDownload() {
    if (!dlSessionId.value || dlState.value === 'idle') return
    _pollActive = true
    _pollTimer = null
    downloadApi.downloadStatus(dlSessionId.value).then((d) => {
      if (!_pollActive) return
      _pollRetryCount = 0
      dlCurrent.value = d.current
      dlTotal.value = d.total
      if (d.status === 'done') {
        dlState.value = 'done'
      } else if (d.status === 'downloading') {
        _pollTimer = setTimeout(pollDownload, 1000)
      } else if (d.status === 'paused') {
        dlState.value = 'paused'
      } else if (d.status === 'error') {
        dlState.value = 'error'
      }
    }).catch(() => {
      if (!_pollActive) return
      _pollRetryCount++
      if (_pollRetryCount >= MAX_POLL_RETRIES) {
        dlState.value = 'error'
        useToastStore().error(`下载状态查询失败，已重试${MAX_POLL_RETRIES}次`)
        return
      }
      const delay = Math.min(2000 * Math.pow(2, _pollRetryCount - 1), 30000)
      _pollTimer = setTimeout(pollDownload, delay)
    })
  }

  function cancelPoll() {
    _pollActive = false
    if (_pollTimer) {
      clearTimeout(_pollTimer)
      _pollTimer = null
    }
  }

  async function pauseDownload() {
    if (!dlSessionId.value) return
    await downloadApi.downloadPause(dlSessionId.value)
    dlState.value = 'paused'
  }

  async function resumeDownload() {
    if (!dlSessionId.value) return
    await downloadApi.downloadResume(dlSessionId.value)
    dlState.value = 'running'
    pollDownload()
  }

  function saveFile() {
    if (dlSessionId.value) {
      window.location.href = downloadApi.downloadFileUrl(dlSessionId.value)
    }
  }

  async function loadSavedBooks() {
    try {
      const d = await downloadApi.listSavedBooks()
      savedBooks.value = d.books || []
    } catch {
      savedBooks.value = []
    }
  }

  return {
    searchQuery,
    searchLoading,
    searchResults,
    searchError,
    bookCounts,
    selectedBook,
    dlState,
    dlCurrent,
    dlTotal,
    dlSessionId,
    savedBooks,
    search,
    selectBook,
    resetSearch,
    startDownload,
    pollDownload,
    cancelPoll,
    pauseDownload,
    resumeDownload,
    saveFile,
    loadSavedBooks,
  }
})
