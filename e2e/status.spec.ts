import { test, expect } from '@playwright/test'
import { as } from './helpers'

test.use(as('meena'))

test('an unknown link shows page not found', async ({ page }) => {
  await page.goto('/c/no-such-page')
  await expect(page.getByText('Page not found')).toBeVisible()
  await page.getByRole('link', { name: 'Back to feed' }).click()
  await expect(page).toHaveURL(/\/c\/?$/)
})

test('losing the connection shows the offline screen and keeps the page', async ({ page, context }) => {
  await page.goto('/c')
  const feed = page.getByRole('heading', { name: 'Feed' })
  await expect(feed).toBeVisible()
  await context.setOffline(true)
  await expect(page.getByText("You're offline")).toBeVisible()
  await context.setOffline(false)
  await expect(page.getByText("You're offline")).toHaveCount(0)
  await expect(page.locator('a[href*="/c/threads/"]').first()).toBeVisible()
})
