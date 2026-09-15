import { getJson, postJson, del, streamNdjson } from './httpClient.js'
let requestTimeoutMs = 135000
let contentTimeoutMs = 615000

function toConfig(c) {
  if (Number.isFinite(c.request_timeout_seconds) && c.request_timeout_seconds > 0) {
    requestTimeoutMs = c.request_timeout_seconds * 1000
  }
  if (Number.isFinite(c.content_timeout_seconds)) contentTimeoutMs = c.content_timeout_seconds * 1000
  return { activeProviderId: c.active_provider_id, providers: c.providers }
}

// Maps the app-level interface to concrete FastAPI endpoints. Keep field names
// snake_case on the wire (Python-friendly) and adapt to camelCase here so the
// React side stays idiomatic. This file is the single source of truth for the
// HTTP contract the backend must satisfy.

const toSession = (s) => ({
  id: s.id,
  title: s.title,
  createdAt: s.created_at,
  updatedAt: s.updated_at,
})

const toMessage = (m) => ({
  id: m.id,
  role: m.role,
  content: m.content,
  sources: (m.citations || []).map((c, i) => ({
    ...c,
    id: `${m.id}_source_${i}`,
    url: c.deep_link || c.youtube_url,
  })),
  artifacts: m.artifacts || [],
  warnings: m.warnings || [],
  createdAt: m.created_at,
})

export const realApi = {
  async getHealth() {
    return getJson('/health')
  },

  async getConfig() {
    const c = await getJson('/config')
    return toConfig(c)
  },

  async setProvider(providerId) {
    const c = await postJson('/config/provider', { provider_id: providerId })
    return toConfig(c)
  },

  async listSessions() {
    const rows = await getJson('/sessions')
    return rows.map(toSession)
  },

  async getMessages(sessionId) {
    const rows = await getJson(`/sessions/${sessionId}/messages`)
    return rows.map(toMessage)
  },

  async deleteSession(sessionId) {
    await del(`/sessions/${sessionId}`)
  },

  // Render Pi model deltas as they arrive through the backend proxy.
  sendMessageStream({ sessionId, content, providerId }, handlers) {
    const controller = new AbortController()
    let cancelStream = null
    ;(async () => {
      try {
        let id = sessionId
        if (!id) {
          const session = await postJson('/sessions', { title: content.slice(0, 100) }, { signal: controller.signal })
          if (controller.signal.aborted) return
          id = session.id
          handlers.onSession?.(toSession(session))
        }
        if (controller.signal.aborted) return
        cancelStream = streamNdjson(`/sessions/${id}/messages/stream`,
          { content, provider_id: providerId }, event => {
            switch (event.type) {
              case 'status': handlers.onStatus?.(event.text); break
              case 'delta': handlers.onDelta?.(event.text); break
              case 'answer': handlers.onAnswer?.(event.text); break
              case 'sources': handlers.onSources?.((event.sources || []).map((c, i) => ({ ...c, id: `${id}_source_${i}`, url: c.deep_link || c.youtube_url }))); break
              case 'artifact': handlers.onArtifact?.(event.artifact); break
              case 'warnings': handlers.onWarnings?.(event.warnings); break
              case 'done': handlers.onDone?.(event.message_id); break
              case 'error': handlers.onError?.(event.message); break
            }
          }, { timeoutMs: /\b(essay|ship\s*30|html|css|one[- ]pager|markdown|document|artifact)\b/i.test(content) ? contentTimeoutMs : requestTimeoutMs })
      } catch (e) {
        if (!controller.signal.aborted) handlers.onError?.(e.message || 'Could not get an answer.')
      }
    })()
    return () => {
      controller.abort()
      cancelStream?.()
    }
  },
}
