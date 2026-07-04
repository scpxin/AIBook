import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SavedBook } from '../api/client'
import * as downloadApi from '../api/download'

export interface DownloadSession {
  session_id: string
  book_id: string
  title: string
  status: string
  current: number
  total: number
}

export const useDownloadStore = defineStore('download', () => {
  const searchQuery = ref('')
  const searchLoading = ref(false)
  const searchResults = ref<any[]>([])
  const searchError = ref('')
  const bookCounts = ref<Record<string, string>>({})
  const selectedBook = ref<any>(null)
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
        if (info && info.book_id) {
          selectedBook.value = info
          searchLoading.value = false
          return
        }
      }
      const data = await downloadApi.searchBooks(searchQuery.value)
      searchResults.value = data.books || []
      searchResults.value.forEach(b => {
        downloadApi.directoryApi(b.book_id).then(d => {
          bookCounts.value[b.book_id] = d.total + ' 章'
        }).catch(() => {})
      })
    } catch (e: any) {
      searchError.value = e.message
    }
    searchLoading.value = false
  }

  function selectBook(b: any) {
    selectedBook.value = {
      book_id: b.book_id,
      title: b.title || b.book_name,
      author: b.author,
      count: bookCounts.value[b.book_id],
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
    dlState.value = 'running'
    dlCurrent.value = 0
    try {
      const d = await downloadApi.downloadStart(selectedBook.value.book_id, selectedBook.value.title)
      dlSessionId.value = d.session_id
      pollDownload()
    } catch (e: any) {
      dlState.value = 'idle'
      alert('启动下载失败: ' + e.message)
    }
  }

  async function pollDownload() {
    if (!dlSessionId.value || dlState.value === 'idle') return
    try {
      const d = await downloadApi.downloadStatus(dlSessionId.value)
      dlCurrent.value = d.current
      dlTotal.value = d.total
      if (d.status === 'done') {
        dlState.value = 'done'
      } else if (d.status === 'downloading') {
        setTimeout(pollDownload, 1000)
      } else if (d.status === 'paused') {
        dlState.value = 'paused'
      } else if (d.status === 'error') {
        dlState.value = 'error'
      }
    } catch {
      setTimeout(pollDownload, 2000)
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
    pauseDownload,
    resumeDownload,
    saveFile,
    loadSavedBooks,
  }
})
