import { createRouter, createWebHistory } from 'vue-router'

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
  ],
})

export default router
