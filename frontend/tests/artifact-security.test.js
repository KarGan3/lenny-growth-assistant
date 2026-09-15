import test from 'node:test'
import assert from 'node:assert/strict'
import { JSDOM } from 'jsdom'
const dom = new JSDOM('')
globalThis.window = dom.window
const { sanitizeArtifactHtml, buildSandboxSrcDoc } = await import('../src/lib/sanitize.js')

test('untrusted HTML cannot retain executable and embedding elements', () => {
  const clean = sanitizeArtifactHtml('<script>alert(1)</script><img src="x" onerror="alert(1)"><iframe src="https://evil.test"></iframe><form><input></form><a href="javascript:alert(1)">bad</a>')
  const doc = new JSDOM(clean).window.document
  assert.equal(doc.querySelector('script,iframe,form,input'), null)
  assert.equal(doc.querySelector('[onerror]'), null)
  assert.equal(doc.querySelector('a').hasAttribute('href'), false)
})

test('artifact document blocks external requests, forms and base URL changes', () => {
  const doc = new JSDOM(buildSandboxSrcDoc('<style>p{color:red}</style><p>Safe content</p>')).window.document
  const csp = doc.querySelector('meta[http-equiv="Content-Security-Policy"]').content
  assert.match(csp, /default-src 'none'/)
  assert.match(csp, /form-action 'none'/)
  assert.match(csp, /base-uri 'none'/)
  assert.match(csp, /img-src data:/)
  assert.ok(doc.querySelector('p'))
})
