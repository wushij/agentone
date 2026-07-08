import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

import { warmBrandIconCache } from '@/utils/brandIconCache'
import App from './App.vue'
import router from './router'

import '@/styles/theme.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/styles/global.css'
import '@/styles/layout-shell.css'
import '@/styles/layout-sidebar.css'
import '@/styles/view-page.css'
import '@/styles/chat-markdown.css'
import '@/styles/chat-dark.css'
import 'highlight.js/styles/github-dark.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

void warmBrandIconCache()

app.mount('#app')
