const CACHE = `crecheconnect${location.search}`

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) =>
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key.startsWith('crecheconnect?build=') && key !== CACHE).map((key) => caches.delete(key))))
			.then(() => self.clients.claim()),
	),
)

self.addEventListener('fetch', (event) => {
	const { request } = event
	const url = new URL(request.url)
	if (request.method !== 'GET' || url.origin !== location.origin) return
	const key = request.mode === 'navigate' ? '/c' : url.pathname.startsWith('/assets/') ? request : null
	if (!key) return
	event.respondWith((async () => {
		const cache = await caches.open(CACHE)
		const hit = await cache.match(key)
		if (hit && url.pathname.startsWith('/assets/creche_connect/frontend/assets/')) return hit
		try {
			const response = await fetch(request)
			if (response.ok && !response.redirected) event.waitUntil(cache.put(key, response.clone()))
			return response
		} catch (error) {
			if (hit) return hit
			throw error
		}
	})())
})

self.addEventListener('push', (event) => {
	const { title, body, url } = event.data.json()
	event.waitUntil(self.registration.showNotification(title, { body, data: url, tag: url, icon: '/assets/creche_connect/pwa/icon-192.png?v=2' }))
})

self.addEventListener('notificationclick', (event) => {
	event.notification.close()
	const url = event.notification.data
	event.waitUntil(
		self.clients.matchAll({ type: 'window' }).then((windows) => {
			const open = windows.find((w) => new URL(w.url).pathname.startsWith('/c'))
			return open ? open.navigate(url).then((w) => w?.focus()) : self.clients.openWindow(url)
		}),
	)
})
