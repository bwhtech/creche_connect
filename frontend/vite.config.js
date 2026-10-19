import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
	plugins: [
		frappeui({
			frontendRoute: '/samvaad',
			frappeProxy: true,
			jinjaBootData: true,
			buildConfig: {
				indexHtmlPath: '../samvaad/www/samvaad.html',
				outDir: '../samvaad/public/frontend',
				baseUrl: '/assets/samvaad/frontend/',
			},
		}),
		vue(),
	],
})
