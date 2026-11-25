import { test, expect } from '@playwright/test'
import { as } from './helpers'

test.use(as('meena'))

test('the app shows a skeleton while boot data is loading', async ({ page }) => {
  let releaseBoot!: () => void
  const bootPaused = new Promise<void>((resolve) => (releaseBoot = resolve))
  await page.route('**/api/method/creche_connect.api.get_boot**', async (route) => {
    await bootPaused
    await route.continue()
  })

  await page.goto('/c', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('app-loading-skeleton')).toBeVisible()
  await expect(page.locator('.animate-spin')).toHaveCount(0)
  releaseBoot()
})
