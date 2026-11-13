import { test, expect } from '@playwright/test'
import { api, as } from './helpers'

const topic = `Bodh Gaya creche visit ${Date.now()}`
let threadUrl = ''

test.describe.serial('a thread reaches its audience', () => {
  test.describe(() => {
    test.use(as('anita'))
    test('admin starts a thread for Bodh Gaya', async ({ page }) => {
      await page.goto('/c/new')
      await page.getByLabel('Topic').fill(topic)
      await page.locator('.ProseMirror').first().fill('Please share the attendance register before Friday.')
      await page.getByLabel('Search places').fill('Bodh Gaya')
      await page.getByLabel('Send to Bodh Gaya').click()
      await page.getByRole('button', { name: 'Start thread' }).click()
      await page.waitForURL(/\/c\/threads\//)
      threadUrl = page.url()
      await expect(page.getByRole('heading', { name: topic })).toBeVisible()
    })
  })

  test.describe(() => {
    test.use(as('meena'))
    test('volunteer in Bodh Gaya sees it and replies', async ({ page }) => {
      await page.goto('/c/')
      await page.getByText(topic).click()
      await page.locator('.ProseMirror').last().fill('Register shared with the block office.')
      await page.keyboard.press('Control+Enter')
      await expect(page.getByText('1 reply')).toBeVisible()
    })
  })

  test.describe(() => {
    test.use(as('anita'))
    test('admin sees the reply, then deletes the thread', async ({ page }) => {
      await page.goto(threadUrl)
      await expect(page.getByText('Register shared with the block office.')).toBeVisible()
      await api(page, 'creche_connect.api.delete_message', {
        doctype: 'CrecheConnect Thread',
        name: threadUrl.split('/').pop(),
      })
    })
  })
})
