import path from 'node:path'
import { test, expect } from '@playwright/test'
import { api, as } from './helpers'

test.use(as('anita'))

const title = `Creche safety checklist ${Date.now()}`

test.afterEach(async ({ page }) => {
  for (const r of await api(page, 'frappe.client.get_list', { doctype: 'CrecheConnect Resource', filters: { title } }))
    await api(page, 'frappe.client.delete', { doctype: 'CrecheConnect Resource', name: r.name })
})

test('a new resource is not pinned to the sidebar', async ({ page }) => {
  await page.goto('/c/resources')
  await page.getByRole('button', { name: 'Add resource' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Title').fill(title)
  await dialog.getByRole('textbox', { name: 'Link' }).fill('https://example.org/creche-safety')
  await dialog.getByRole('button', { name: 'Add this link' }).click()
  await dialog.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('Resource added')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button', { name: title })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main' }).getByText(title)).toHaveCount(0)
})

test('an uploaded file opens for members only', async ({ page, browser }) => {
  await page.goto('/c/resources')
  await page.getByRole('button', { name: 'Add resource' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Title').fill(title)
  const chooser = page.waitForEvent('filechooser')
  await dialog.getByRole('button', { name: 'Upload file' }).click()
  await (await chooser).setFiles({ name: 'safety-checklist.txt', mimeType: 'text/plain', buffer: Buffer.from('Check the gate') })
  await expect(dialog.getByPlaceholder('safety-checklist.txt')).toBeVisible()
  await dialog.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('Resource added')).toBeVisible()
  const [{ name }] = await api(page, 'frappe.client.get_list', { doctype: 'CrecheConnect Resource', filters: { title } })
  const [file] = (await api(page, 'frappe.client.get', { doctype: 'CrecheConnect Resource', name })).files
  expect(file.url).toMatch(/^\/private\/files\//)
  const member = await browser.newContext(as('meena'))
  expect((await member.request.get(file.url)).status()).toBe(200)
  const guest = await browser.newContext({ storageState: { cookies: [], origins: [] } })
  expect((await guest.request.get(file.url)).status()).toBe(403)
})

test('one resource holds several files and links', async ({ page }) => {
  await page.goto('/c/resources')
  await page.getByRole('button', { name: 'Add resource' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Title').fill(title)
  for (const name of ['checklist-english.txt', 'checklist-hindi.txt']) {
    const chooser = page.waitForEvent('filechooser')
    await dialog.getByRole('button', { name: 'Upload file' }).click()
    await (await chooser).setFiles({ name, mimeType: 'text/plain', buffer: Buffer.from(name) })
    await expect(dialog.getByPlaceholder(name)).toBeVisible()
  }
  await dialog.getByRole('textbox', { name: 'Link' }).fill('https://example.org/creche-safety')
  await dialog.getByRole('button', { name: 'Add this link' }).click()
  await dialog.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('Resource added')).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: title }).click()
  await expect(page.getByText('3 files').last()).toBeVisible()
  await expect(page.getByRole('link', { name: 'checklist-english.txt' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'checklist-hindi.txt' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'example.org/creche-safety' })).toBeVisible()
})

test('a word file opens in the viewer instead of downloading', async ({ page }) => {
  await page.goto('/c/resources')
  await page.getByRole('button', { name: 'Add resource' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Title').fill(title)
  const chooser = page.waitForEvent('filechooser')
  await dialog.getByRole('button', { name: 'Upload file' }).click()
  await (await chooser).setFiles(path.join(__dirname, 'fixtures/safety-checklist.docx'))
  await expect(dialog.getByPlaceholder('safety-checklist.docx')).toBeVisible()
  await dialog.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('Resource added')).toBeVisible()
  await page.getByRole('link', { name: 'safety-checklist.docx' }).click()
  const viewer = page.getByRole('dialog', { name: 'safety-checklist.docx' })
  await expect(viewer.getByText('Check the gate before children arrive.')).toBeVisible()
  await viewer.getByRole('button', { name: 'Close' }).click()
  await expect(viewer).toHaveCount(0)
})
