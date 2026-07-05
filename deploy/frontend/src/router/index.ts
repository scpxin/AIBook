import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/fanqie/'),
  routes: [
    {
      path: '/',
      redirect: '/download',
    },
    {
      path: '/download',
      name: 'download',
      component: () => import('../views/Download.vue'),
    },
    {
      path: '/create',
      name: 'create',
      component: () => import('../views/Create.vue'),
    },
    {
      path: '/craft',
      name: 'craft',
      component: () => import('../views/Craft.vue'),
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
  ],
})

export default router
