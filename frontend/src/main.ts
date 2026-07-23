import { createApp } from 'vue'
import { warmBrandIconCache } from '@/utils/brandIconCache'
import App from './App.vue'
import { setupPlugins } from '@/plugins'

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

setupPlugins(app)

void warmBrandIconCache()

app.mount('#app')
