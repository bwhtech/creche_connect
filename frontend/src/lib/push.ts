import { ref } from 'vue'
import { call, frappeRequest } from 'frappe-ui'

export const pushSupported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
export const pushOn = ref(false)

const registration = () => navigator.serviceWorker.getRegistration('/c')
const subscription = async () => (await registration())?.pushManager.getSubscription()
const toBytes = (key: string) => Uint8Array.from(atob(key.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0))

export async function checkPush() {
  if (pushSupported) pushOn.value = Notification.permission === 'granted' && !!(await subscription())
}

export async function enablePush() {
  if ((await Notification.requestPermission()) !== 'granted') throw new Error('Notifications are blocked. Allow them for CrecheConnect in your phone or browser settings.')
  const key = await frappeRequest({ url: 'creche_connect.push.get_public_key', method: 'GET' })
  const sub = await (await registration())!.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toBytes(key) })
  await call('creche_connect.push.subscribe', { subscription: sub.toJSON() })
  pushOn.value = true
}

export async function disablePush() {
  const sub = pushSupported && (await subscription())
  if (sub) {
    await call('creche_connect.push.unsubscribe', { endpoint: sub.endpoint })
    await sub.unsubscribe()
  }
  pushOn.value = false
}
