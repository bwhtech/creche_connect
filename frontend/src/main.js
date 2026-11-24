import { createApp, h } from 'vue'
import { FrappeUI, FrappeUIProvider, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './style.css'

setConfig('systemTimezone', window.system_timezone ?? null)
setConfig('maxFileSize', window.max_file_size ?? null)

document.addEventListener(
  'play',
  ({ target: v }) => v instanceof HTMLVideoElement && v.src.includes('#t=') && !v.dataset.rewound && ((v.dataset.rewound = '1'), (v.currentTime = 0)),
  true,
)

createApp({ render: () => h(FrappeUIProvider, () => h(App)) }).use(router).use(FrappeUI).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) navigator.serviceWorker.register(`/crecheconnect-sw.js?build=${new URL(import.meta.url).pathname.split('/').pop()}`, { scope: '/c' })
