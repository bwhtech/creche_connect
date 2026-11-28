import fs from 'node:fs'
import path from 'node:path'
import { test, expect } from '@playwright/test'
import { api, as } from './helpers'

test.use(as('meena'))

const photo = path.join(__dirname, 'fixtures/illustration.png')

test('an uploaded photo is stored as a smaller jpeg', async ({ page }) => {
  await page.goto('/c/')
  const { image: original } = await page.evaluate(() => fetch('/api/method/creche_connect.api.get_boot').then((r) => r.json()).then((r) => r.message.me))
  try {
    await page.getByRole('button', { name: /Meena/ }).last().click()
    await page.getByRole('menuitem', { name: /photo/ }).click()
    const uploaded = page.waitForResponse((r) => r.url().includes('upload_file'))
    await page.locator('input[type=file][accept="image/*"]').setInputFiles(photo)
    const { message } = await (await uploaded).json()
    expect(message.file_url).toMatch(/\.jpg$/)
    expect(message.file_size).toBeLessThan(fs.statSync(photo).size / 2)
  } finally {
    await api(page, 'creche_connect.api.set_avatar', { image: original || null })
  }
})
