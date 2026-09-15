import { test, expect } from '@playwright/test'
import path from 'node:path'

test('requested palette appears in page, composer and button states', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('body')).toHaveCSS('background-color','rgb(15, 48, 64)')
  await expect(page.getByRole('textbox',{name:'Message the assistant'}).locator('..')).toHaveCSS('background-color','rgb(70, 72, 88)')
  await page.getByRole('textbox',{name:'Message the assistant'}).fill('How can I improve activation?')
  await expect(page.getByRole('button',{name:'Send message',exact:true})).toHaveCSS('background-color','rgb(217, 155, 127)')
  await page.getByRole('button',{name:'Send message',exact:true}).hover()
  await expect(page.getByRole('button',{name:'Send message',exact:true})).toHaveCSS('background-color','rgb(165, 111, 99)')
  await page.screenshot({path:path.resolve('../docs/screenshots/palette-desktop.png')})
})
