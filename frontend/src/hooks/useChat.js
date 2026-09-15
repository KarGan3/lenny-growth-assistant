import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/index.js'

let tmp = 0
const tempId = (p) => `tmp_${p}_${++tmp}`

// Central chat state: session list, the active thread, provider selection, and
// the streaming lifecycle. Components stay presentational; all orchestration
// lives here.
export function useChat({ onArtifact } = {}) {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [loadingThread, setLoadingThread] = useState(false)
  const [error, setError] = useState(null)

  const [providers, setProviders] = useState([])
  const [activeProviderId, setActiveProviderId] = useState(null)

  const cancelRef = useRef(null)
  const assistantIdRef = useRef(null)

  // ---- initial load --------------------------------------------------------
  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const cfg = await api.getConfig()
        if (!alive) return
        setProviders(cfg.providers)
        setActiveProviderId(cfg.activeProviderId)
      } catch {
        /* provider UI just stays empty; non-fatal */
      }
      try {
        const rows = await api.listSessions()
        if (alive) setSessions(rows)
      } catch (e) {
        if (alive) setError(e.message)
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  const patchAssistant = useCallback((updater) => {
    const assistantId = assistantIdRef.current
    setMessages((prev) =>
      prev.map((m) => (m.id === assistantId ? updater(m) : m))
    )
  }, [])

  // ---- actions -------------------------------------------------------------
  const newChat = useCallback(() => {
    cancelRef.current?.()
    cancelRef.current = null
    setIsStreaming(false)
    setActiveSessionId(null)
    setMessages([])
    setError(null)
  }, [])

  const selectSession = useCallback(
    async (id) => {
      if (id === activeSessionId) return
      cancelRef.current?.()
      cancelRef.current = null
      setIsStreaming(false)
      setActiveSessionId(id)
      setError(null)
      setLoadingThread(true)
      try {
        const rows = await api.getMessages(id)
        setMessages(rows)
      } catch (e) {
        setError(e.message)
        setMessages([])
      } finally {
        setLoadingThread(false)
      }
    },
    [activeSessionId]
  )

  const deleteSession = useCallback(
    async (id) => {
      try {
        await api.deleteSession(id)
      } catch (e) {
        setError(e.message)
        return
      }
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (id === activeSessionId) newChat()
    },
    [activeSessionId, newChat]
  )

  const setProvider = useCallback(async (id) => {
    try {
      const cfg = await api.setProvider(id)
      setProviders(cfg.providers)
      setActiveProviderId(cfg.activeProviderId)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  const sendMessage = useCallback(
    (raw) => {
      const content = (raw || '').trim()
      if (!content || isStreaming) return

      const userMsg = {
        id: tempId('u'),
        role: 'user',
        content,
        sources: [],
        artifacts: [],
        createdAt: new Date().toISOString(),
      }
      const assistantId = tempId('a')
      assistantIdRef.current = assistantId
      const assistantMsg = {
        id: assistantId,
        role: 'assistant',
        content: '',
        sources: [],
        artifacts: [],
        pending: true,
        createdAt: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setError(null)

      cancelRef.current = api.sendMessageStream(
        { sessionId: activeSessionId, content, providerId: activeProviderId },
        {
          onSession: (session) => {
            setActiveSessionId(session.id)
            setSessions((prev) =>
              prev.some((s) => s.id === session.id) ? prev : [session, ...prev]
            )
          },
          onDelta: (text) =>
            patchAssistant((m) => ({ ...m, content: m.content + text })),
          onAnswer: (text) => patchAssistant((m) => ({ ...m, content: text })),
          onStatus: (status) => patchAssistant((m) => ({ ...m, status })),
          onSources: (sources) => patchAssistant((m) => ({ ...m, sources })),
          onWarnings: (warnings) => patchAssistant((m) => ({ ...m, warnings })),
          onArtifact: (artifact) => {
            patchAssistant((m) => ({ ...m, artifacts: [...m.artifacts, artifact] }))
            onArtifact?.(artifact)
          },
          onDone: (messageId) => {
            patchAssistant((m) => ({ ...m, pending: false, id: messageId || m.id }))
            assistantIdRef.current = null
            cancelRef.current = null
            setIsStreaming(false)
          },
          onError: (msg) => {
            patchAssistant((m) => ({ ...m, pending: false, error: true, errorMessage: msg }))
            setError(msg)
            assistantIdRef.current = null
            cancelRef.current = null
            setIsStreaming(false)
          },
        }
      )
    },
    [activeSessionId, activeProviderId, isStreaming, patchAssistant, onArtifact]
  )

  const stop = useCallback(() => {
    cancelRef.current?.()
    cancelRef.current = null
    patchAssistant((m) => ({ ...m, pending: false }))
    assistantIdRef.current = null
    setIsStreaming(false)
  }, [patchAssistant])

  const activeProvider = providers.find((p) => p.id === activeProviderId) || null

  return {
    sessions,
    activeSessionId,
    messages,
    isStreaming,
    loadingThread,
    error,
    providers,
    activeProvider,
    setProvider,
    newChat,
    selectSession,
    deleteSession,
    sendMessage,
    stop,
    dismissError: () => setError(null),
  }
}
