import { config } from '../config.js'

// A thin fetch wrapper. Two jobs: prefix every path with the API base, and
// turn every failure into a single ApiError shape the UI can render.

export class ApiError extends Error {
  constructor(message, { status, code, detail } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
  }
}

function url(path) {
  return `${config.apiBaseUrl}${path}`
}

async function toError(res) {
  let body = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON error body */
  }
  const message =
    body?.detail?.message || body?.detail || body?.message || res.statusText || 'Request failed'
  return new ApiError(message, { status: res.status, code: body?.detail?.code || body?.code })
}

export async function getJson(path) {
  let res
  try {
    res = await fetch(url(path), { headers: { Accept: 'application/json' } })
  } catch (e) {
    throw new ApiError('Could not reach the server. Is the backend running?', { code: 'network' })
  }
  if (!res.ok) throw await toError(res)
  return res.json()
}

export async function postJson(path, body, { signal } = {}) {
  let res
  try {
    res = await fetch(url(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body ?? {}),
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Could not reach the server. Is the backend running?', { code: 'network' })
  }
  if (!res.ok) throw await toError(res)
  return res.json()
}

export async function del(path) {
  let res
  try {
    res = await fetch(url(path), { method: 'DELETE' })
  } catch (e) {
    throw new ApiError('Could not reach the server. Is the backend running?', { code: 'network' })
  }
  if (!res.ok) throw await toError(res)
}

/**
 * POST a request whose response is a newline-delimited JSON stream and invoke
 * `onEvent` for each parsed object. Returns a function that aborts the stream.
 *
 * Wire contract (each line is one JSON object):
 *   {"type":"session","session":{...}}   // emitted first if a session was created
 *   {"type":"delta","text":"..."}        // 0..n incremental text chunks
 *   {"type":"sources","sources":[...]}   // grounding citations
 *   {"type":"artifact","artifact":{...}} // a renderable markdown/html artifact
 *   {"type":"done","messageId":"..."}
 *   {"type":"error","message":"..."}
 */
export function streamNdjson(path, body, onEvent, { timeoutMs = 135000 } = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => {
    controller.abort()
    onEvent({ type: 'error', message: 'The answer took too long. Please try again.' })
  }, timeoutMs)
  let terminal = false
  const deliver = (event) => {
    if (event.type === 'done' || event.type === 'error') terminal = true
    onEvent(event)
  }

  ;(async () => {
    let res
    try {
      res = await fetch(url(path), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' },
        body: JSON.stringify(body ?? {}),
        signal: controller.signal,
      })
    } catch (e) {
      if (e.name === 'AbortError') return
      onEvent({ type: 'error', message: 'Could not reach the server. Is the backend running?' })
      return
    }

    if (!res.ok || !res.body) {
      const err = await toError(res).catch(() => new ApiError('Stream failed'))
      onEvent({ type: 'error', message: err.message })
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let nl
        while ((nl = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, nl).trim()
          buffer = buffer.slice(nl + 1)
          if (line) {
            try {
              deliver(JSON.parse(line))
            } catch {
              /* ignore malformed line */
            }
          }
        }
      }
      const tail = buffer.trim()
      if (tail) {
        try {
          deliver(JSON.parse(tail))
        } catch {
          /* ignore */
        }
      }
      if (!terminal) onEvent({ type: 'error', message: 'The answer stream ended early. Please try again.' })
    } catch (e) {
      if (e.name !== 'AbortError') onEvent({ type: 'error', message: 'Stream interrupted.' })
    }
  })().finally(() => clearTimeout(timeout))

  return () => {
    clearTimeout(timeout)
    controller.abort()
  }
}
