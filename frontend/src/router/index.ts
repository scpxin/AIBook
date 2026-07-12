import { createRouter, createWebHistory } from 'vue-router'
import { useModuleSaveStore } from '../stores/moduleSave'
import { setupConfirm } from '../composables/useConfirm'
import { flushAllSaves } from '../composables/useSaveRegistry'

const router = createRouter({
  history: createWebHistory('/fanqie/'),
  routes: [
    {
      path: '/',
      redirect: '/create-v2',
    },
    {
      path: '/download',
      name: 'download',
      component: () => import('../views/Download.vue'),
    },
    {
      path: '/create-v2',
      name: 'create-v2',
      component: () => import('../views/CreateV2.vue'),
    },
    {
      path: '/create-v2/:module',
      name: 'create-v2-module',
      component: () => import('../views/CreateV2.vue'),
    },
    {
      path: '/create-v2/writing/:chapterId',
      name: 'create-v2-writing',
      component: () => import('../views/WritingView.vue'),
    },
    {
      path: '/modules',
      name: 'modules',
      component: () => import('../views/ModulesOverview.vue'),
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('../views/TemplateLibrary.vue'),
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('../views/ProjectsOverview.vue'),
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const isFromCreateV2 = from.path.startsWith('/create-v2')
  const isToCreateV2 = to.path.startsWith('/create-v2')

  if (isFromCreateV2 && !isToCreateV2) {
    const store = useModuleSaveStore()
    const pid = from.query.projectId as string
    if (pid && store.hasUnsavedChanges(pid)) {
      const confirm = setupConfirm()
      const ok = await confirm.confirm({
        title: '未保存的更改',
        message: `当前项目有 ${store.getGlobalUnsavedCount()} 个模块的数据未保存。`,
        detail: '点击"保存并离开"将自动保存所有模块数据后离开',
        confirmText: '保存并离开',
        cancelText: '取消',
        type: 'warning',
      })
      if (!ok) {
        next(false)
        return
      }
      try {
        await flushAllSaves()
      } catch (_e) { /* continue navigation even if save fails */ }
    }
  }

  next()
})

export default router
