<template>
  <div class="header">
    <h1>AI创作平台</h1>
    <p>智能写作 · 一站式创作体验</p>
    <button class="settings-btn" @click="showSettings = true">&#9881; 模型配置</button>
  </div>

  <TabBar />

  <div class="container">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>

  <ModelConfig v-if="showSettings" @close="showSettings = false" />
  <ToastContainer />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TabBar from './components/TabBar.vue'
import ModelConfig from './components/ModelConfig.vue'
import ToastContainer from './components/ToastContainer.vue'

const showSettings = ref(false)
</script>
