const CACHE = `crecheconnect${location.search}`

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) =>
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => self.clients.claim()),
	),
)

self.addEventListener('fetch', (event) => {
	const { request } = event
	const url = new URL(request.url)
	if (request.method !== 'GET' || url.origin !== location.origin) return
	const key = request.mode === 'navigate' ? '/c' : url.pathname.startsWith('/assets/') ? request : null
	if (!key) return
	event.respondWith(
		fetch(request)
			.then((response) => {
				if (response.ok && !response.redirected) {
					const copy = response.clone()
					caches.open(CACHE).then((cache) => cache.put(key, copy))
				}
				return response
			})
			.catch(() => caches.match(key)),
	)
})

self.addEventListener('push', (event) => {
	const { title, body, url } = event.data.json()
	event.waitUntil(self.registration.showNotification(title, { body, data: url, tag: url, icon: '/assets/creche_connect/pwa/icon-192.png' }))
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
