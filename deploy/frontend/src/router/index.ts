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
  ],
})

export default router
