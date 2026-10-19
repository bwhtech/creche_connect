import { createApp } from 'vue'
import { FrappeUI, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './style.css'

setConfig('systemTimezone', window.system_timezone ?? null)

createApp(App).use(router).use(FrappeUI).mount('#app')
