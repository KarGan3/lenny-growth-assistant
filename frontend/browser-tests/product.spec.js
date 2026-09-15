import { test, expect } from '@playwright/test'

test('real app starts in local mode and supports mobile navigation', async ({ page }) => {
  const errors=[]
  page.on('pageerror',e=>errors.push(e.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Ask Lenny/ })).toBeVisible()
  await expect(page.getByRole('button', { name: /Ollama/ })).toBeVisible()
  await expect(page.getByText('Running on mock data.')).toHaveCount(0)
  await page.setViewportSize({width:390,height:844})
  await page.getByRole('button',{name:'Open menu'}).click()
  await expect(page.getByRole('button',{name:'New chat',exact:true}).last()).toBeVisible()
  await page.getByRole('button',{name:'Close menu'}).last().click()
  await expect(page.getByRole('textbox',{name:'Message the assistant'})).toBeVisible()
  expect(errors).toEqual([])
})

test('HTML viewer blocks scripts and external requests while retaining styles', async ({ page, request }) => {
  const session=await (await request.post('/api/sessions',{data:{title:'Browser security fixture'}})).json()
  await page.route(`**/api/sessions/${session.id}/messages`,route=>route.fulfill({json:[{
    id:'test-message',role:'assistant',content:'Security test fixture [1].',citations:[],
    artifacts:[{id:'fixture',title:'Protected brief',type:'html',content:'<!doctype html><html><head><style>h1{color:rgb(12,34,56)}</style></head><body><h1>Protected preview</h1><script>window.__ran=true;top.__escaped=true</script><img src="https://evil.test/tracker"><form action="https://evil.test"></form></body></html>'}],
  }]}))
  let external=0
  await page.route('https://evil.test/**',route=>{external++;return route.abort()})
  try {
    await page.goto('/')
    await page.getByRole('button',{name:'Browser security fixture',exact:true}).click()
    await page.getByRole('button',{name:/Protected brief/}).click()
    const frame=page.frameLocator('iframe[title="Protected brief"]')
    await expect(frame.getByRole('heading',{name:'Protected preview'})).toBeVisible()
    await expect(frame.getByRole('heading')).toHaveCSS('color','rgb(12, 34, 56)')
    await expect(page.locator('iframe')).toHaveAttribute('sandbox','')
    expect(await page.evaluate(()=>Boolean(window.__escaped))).toBe(false)
    expect(await frame.locator('body').evaluate(()=>Boolean(window.__ran))).toBe(false)
    await expect(frame.locator('script,form')).toHaveCount(0)
    expect(external).toBe(0)
    await page.getByRole('tab',{name:'Code',exact:true}).click()
    await expect(page.locator('pre').last()).toContainText('<!doctype html>')
  } finally { await request.delete(`/api/sessions/${session.id}`) }
})
