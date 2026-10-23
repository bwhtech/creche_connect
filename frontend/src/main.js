import { createApp, h } from 'vue'
import { FrappeUI, FrappeUIProvider, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './style.css'

setConfig('systemTimezone', window.system_timezone ?? null)

createApp({ render: () => h(FrappeUIProvider, () => h(App)) }).use(router).use(FrappeUI).mount('#app')
