import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
	history: createWebHistory('/samvaad'),
	routes: [
		{ path: '/', component: () => import('./pages/Feed.vue') },
		{ path: '/search', component: () => import('./pages/Search.vue') },
		{ path: '/new', component: () => import('./pages/Compose.vue') },
		{ path: '/threads/:id', component: () => import('./pages/Thread.vue'), props: true },
		{ path: '/users', component: () => import('./pages/Users.vue') },
		{ path: '/resources', component: () => import('./pages/Resources.vue') },
		{ path: '/insights', component: () => import('./pages/Insights.vue') },
	],
})

router.onError((error, to) => {
	if (/dynamically imported module|Importing a module script failed/.test(error.message)) {
		window.location.assign(router.resolve(to).href)
	}
})

export default router
