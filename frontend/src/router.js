import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
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
