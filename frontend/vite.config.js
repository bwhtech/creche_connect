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
				indexHtmlPath: '../crecheconnect/www/c.html',
				outDir: '../crecheconnect/public/frontend',
				baseUrl: '/assets/crecheconnect/frontend/',
			},
		}),
		vue(),
	],
})
