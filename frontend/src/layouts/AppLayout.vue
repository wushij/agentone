<script setup lang="ts">

import { computed } from 'vue'

import { useRoute } from 'vue-router'

import AppHeader from '@/components/layout/AppHeader.vue'

import AppSidebar from '@/components/AppSidebar.vue'

import { useUserStore } from '@/stores/user'



const route = useRoute()

const userStore = useUserStore()



const isFullBleed = computed(() => Boolean(route.meta.fullBleed))

</script>



<template>

  <div class="app-layout-container">

    <el-alert

      v-if="userStore.backendUnavailable"

      type="warning"

      title="后端服务暂时不可用，请确认后端已启动；部分数据可能无法加载。"

      show-icon

      :closable="false"

      class="app-layout__offline-alert"

    />



    <div class="app-layout">

      <AppSidebar />

      <div class="app-layout__main">

        <AppHeader />

        <main class="app-layout__content" :class="{ 'app-layout__content--full': isFullBleed }">

          <router-view />

        </main>

      </div>

    </div>

  </div>

</template>

