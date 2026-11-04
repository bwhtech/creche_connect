import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
	plugins: [
		frappeui({
			frontendRoute: '/c',
			frappeProxy: true,
			jinjaBootData: true,
			buildConfig: {
				indexHtmlPath: '../creche_connect/www/c.html',
				outDir: '../creche_connect/public/frontend',
				baseUrl: '/assets/creche_connect/frontend/',
			},
		}),
		vue(),
	],
})
