import { test, expect } from '@playwright/test'
import { api, as } from './helpers'

test.use(as('anita'))

test('Hindi localizes the interface while preserving authored text and links', async ({ page }) => {
  await page.goto('/c/')
  const originalLanguage = await page.locator('html').getAttribute('lang')
  const { name: thread } = await api(page, 'creche_connect.api.create_thread', {
    title: 'Feed',
    content: '<p><a href="https://example.org/">Share</a></p>',
    places: ['BR-GAY-BDG'],
  })
  try {
    await api(page, 'creche_connect.api.set_language', { language: 'hi' })
    await page.goto(`/c/threads/${thread}`)

    await expect(page.locator('html')).toHaveAttribute('lang', 'hi')
    await expect(page.getByRole('link', { name: 'फ़ीड', exact: true }).first()).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Feed', exact: true })).toBeVisible()
    await expect(page.locator('.rich p').filter({ hasText: /^Share$/ }).first()).toBeVisible()
    await expect(page.getByRole('link', { name: 'Share', exact: true })).toHaveAttribute('href', 'https://example.org/')
  } finally {
    if (originalLanguage) await api(page, 'creche_connect.api.set_language', { language: originalLanguage })
    await api(page, 'creche_connect.api.delete_message', { doctype: 'CrecheConnect Thread', name: thread })
  }
})
