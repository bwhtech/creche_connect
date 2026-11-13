import { test as setup, expect } from '@playwright/test'
import { USERS } from './helpers'

for (const [user, usr] of Object.entries(USERS)) {
  setup(`log in as ${user}`, async ({ page }) => {
    await page.goto('/login')
    const status = await page.evaluate(
      async (body) => (await fetch('/api/method/login', { method: 'POST', body: new URLSearchParams(body) })).status,
      { usr, pwd: process.env.DEMO_PASSWORD || 'crecheconnect123' },
    )
    expect(status).toBe(200)
    await page.context().storageState({ path: `e2e/.auth/${user}.json` })
  })
}
