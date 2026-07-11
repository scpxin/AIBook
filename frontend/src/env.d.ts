/// <reference types="vite/client" />

import type { App } from 'vue'
import type { Router } from 'vue-router'

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $router: Router
  }
}
