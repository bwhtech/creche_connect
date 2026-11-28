import { createApp, h } from 'vue'
import { FrappeUIProvider, dayjs, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import 'dayjs/esm/locale/hi'
import { __, lang } from './lib/translate'
import './style.css'

dayjs.locale(lang)
setConfig('systemTimezone', window.system_timezone ?? null)
setConfig('maxFileSize', window.max_file_size ?? null)

// iOS Safari only applies :active styles when a touchstart listener exists
document.addEventListener('touchstart', () => {}, { passive: true })

const app = createApp({ render: () => h(FrappeUIProvider, () => h(App)) })
app.config.globalProperties.__ = __
app.use(router).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) navigator.serviceWorker.register(`/crecheconnect-sw.js?build=${new URL(import.meta.url).pathname.split('/').pop()}`, { scope: '/c' })
