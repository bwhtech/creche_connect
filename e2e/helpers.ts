import type { Page } from '@playwright/test'

export const USERS = { anita: 'anita@crecheconnect.local', meena: 'meena@crecheconnect.local' }
export const as = (user: keyof typeof USERS) => ({ storageState: `e2e/.auth/${user}.json` })

export const api = (page: Page, method: string, args: object) =>
  page.evaluate(
    async ([method, args]) => {
      const r = await fetch(`/api/method/${method}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': (window as any).csrf_token },
        body: JSON.stringify(args),
      })
      if (!r.ok) throw new Error(`${method} failed: ${r.status}`)
      return (await r.json()).message
    },
    [method, args] as const,
  )
