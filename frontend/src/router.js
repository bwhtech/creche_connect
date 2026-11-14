import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
	history: createWebHistory('/c'),
	routes: [
		{ path: '/', component: () => import('./pages/Feed.vue') },
		{ path: '/search', component: () => import('./pages/Search.vue') },
		{ path: '/new', component: () => import('./pages/Compose.vue') },
		{ path: '/threads/:id', component: () => import('./pages/Thread.vue'), props: true },
		{ path: '/users', component: () => import('./pages/Users.vue') },
		{ path: '/resources', component: () => import('./pages/Resources.vue') },
		{ path: '/insights', component: () => import('./pages/Insights.vue') },
		{ path: '/:path(.*)*', component: () => import('./pages/NotFound.vue') },
	],
})

router.onError((error, to) => {
	if (!/dynamically imported module|Importing a module script failed/.test(error.message)) return
	if (navigator.onLine) window.location.assign(router.resolve(to).href)
	else window.addEventListener('online', () => router.push(to), { once: true })
})

export default router
