import { test, expect } from '@playwright/test'
import fs from 'node:fs/promises'
import path from 'node:path'

// Optional real-output check: supply the session produced by evaluate-local.py.
// Ordinary browser tests do not depend on a pre-existing developer conversation.
test('saved local model artifacts recover, preview, copy and download', async ({ page, request, context }) => {
  const sessionId = process.env.EVALUATION_SESSION_ID
  test.skip(!sessionId, 'Requires an explicitly selected real local demo session')
  const response = await request.get(`/api/sessions/${sessionId}/messages`)
  expect(response.ok()).toBe(true)
  const messages = await response.json()
  const artifacts = messages.flatMap(message => message.artifacts || [])
  expect(artifacts).toHaveLength(Number(process.env.EVALUATION_ARTIFACT_COUNT || 3))
  expect(artifacts.some(artifact => artifact.type === 'html')).toBe(true)
  expect(artifacts.filter(artifact => artifact.type === 'markdown').length).toBeGreaterThanOrEqual(2)
  await context.grantPermissions(['clipboard-read', 'clipboard-write'])
  await page.goto('/')
  const select = () => page.locator(`button[data-session-id="${sessionId}"]`).click()
  await select()
  await page.reload()
  await select()
  const chips = page.getByRole('button', { name: /Open in viewer/ })
  await expect(chips).toHaveCount(artifacts.length)
  for (const [index, artifact] of artifacts.entries()) {
    await expect(chips.nth(index)).toContainText(artifact.title)
    await chips.nth(index).click()
    if (artifact.type === 'html') {
      await expect(page.frameLocator('iframe').locator('h1')).toBeVisible()
      await expect(page.locator('iframe')).toHaveAttribute('sandbox', '')
      await page.screenshot({ path: path.resolve('../docs/screenshots/saved-local-html.png') })
    } else {
      await expect(page.getByRole('heading').last()).toBeVisible()
    }
    await page.getByRole('tab', { name: 'Code', exact: true }).click()
    await expect(page.locator('pre').last()).toHaveText(artifact.content)
    await page.getByRole('button', { name: 'Copy source', exact: true }).click()
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(artifact.content)
    const pendingDownload = page.waitForEvent('download')
    await page.getByRole('button', { name: 'Download artifact', exact: true }).click()
    const download = await pendingDownload
    expect(await fs.readFile(await download.path(), 'utf8')).toBe(artifact.content)
    await page.getByRole('button', { name: 'Close artifact', exact: true }).click()
  }
  await page.screenshot({ path: path.resolve('../docs/screenshots/saved-local-demo.png') })
})
