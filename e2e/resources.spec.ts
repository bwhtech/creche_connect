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
  await dialog.getByLabel('Link').fill('https://example.org/creche-safety')
  await dialog.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('Resource added')).toBeVisible()
  await page.reload()
  await expect(page.getByText(title)).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main' }).getByText(title)).toHaveCount(0)
})
