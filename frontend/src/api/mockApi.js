// In-memory mock adapter. Lets the whole UI run (sessions, streaming, sources,
// artifacts) with ZERO backend, so `npm run dev` shows a working product on a
// fresh clone. Every string below is placeholder fixture data — the real
// backend replaces it with genuine retrieval + generation. Nothing here is a
// factual claim; source snippets are paraphrased summaries for layout only.

let seq = 100
const uid = (p) => `${p}_${++seq}`
const nowIso = () => new Date().toISOString()
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// ---- provider fixtures -----------------------------------------------------
let activeProviderId = 'ollama-llama31'
const providers = [
  { id: 'claude-sonnet', label: 'Claude Sonnet', type: 'cloud', model: 'claude-sonnet-4' },
  { id: 'ollama-llama31', label: 'Llama 3.1 8B', type: 'local', model: 'llama3.1:8b' },
]

// ---- seed sessions ---------------------------------------------------------
const store = {
  sessions: [
    { id: 'sess_demo_1', title: 'How do I find product-market fit?', createdAt: nowIso(), updatedAt: nowIso() },
    { id: 'sess_demo_2', title: 'Growth loops vs. funnels', createdAt: nowIso(), updatedAt: nowIso() },
  ],
  messages: {
    sess_demo_1: [
      { id: 'm1', role: 'user', content: 'How do I know when I have product-market fit?', sources: [], artifacts: [], createdAt: nowIso() },
      {
        id: 'm2',
        role: 'assistant',
        content:
          "Across the transcripts, a few consistent signals come up. Product-market fit tends to show up as **pull rather than push** — retention curves that flatten instead of decaying to zero, organic word-of-mouth, and users who would be genuinely upset if the product went away.\n\nA practical test that recurs is the *\"very disappointed\"* survey: if roughly 40% or more of users say they'd be very disappointed to lose the product, that's a strong early signal.\n\nJust as important is the qualitative side — founders describe a shift from convincing people to try the product to struggling to keep up with demand.",
        sources: [
          { id: 's1', guest: 'Rahul Vohra', title: 'How Superhuman found product-market fit', episode: "Lenny's Podcast", snippet: 'the “very disappointed” benchmark as a leading indicator of fit', url: 'https://github.com/ChatPRD/lennys-podcast-transcripts' },
          { id: 's2', guest: 'Brian Chesky', title: 'Building Airbnb', episode: "Lenny's Podcast", snippet: 'the shift from pushing the product to demand outpacing the team', url: 'https://github.com/ChatPRD/lennys-podcast-transcripts' },
        ],
        artifacts: [],
        createdAt: nowIso(),
      },
    ],
    sess_demo_2: [],
  },
}

// ---- canned response generation -------------------------------------------
function buildReply(content) {
  const q = content.toLowerCase()
  const wantsEssay = /essay|ship\s*30|write|draft|blog|post/.test(q)
  const wantsHtml = /html|landing|one[-\s]?pager|table|snippet|render/.test(q)

  const text =
    "Here's what the transcripts suggest.\n\n" +
    "The strongest teams treat this as a **system**, not a one-off tactic. Three ideas recur:\n\n" +
    "- **Start from the job the user is hiring the product for**, not the feature you want to ship.\n" +
    "- **Instrument the moment of value** so you can see activation, not just sign-ups.\n" +
    "- **Close the loop** — every new user should create a reason for the next one to arrive.\n\n" +
    "The teams that compound are the ones that make that loop *shorter and more reliable* over time, rather than adding new acquisition channels on top of a leaky funnel."

  const sources = [
    { id: uid('s'), guest: 'Elena Verna', title: 'Growth loops and PLG', episode: "Lenny's Podcast", snippet: 'why compounding loops beat linear funnels for durable growth', url: 'https://github.com/ChatPRD/lennys-podcast-transcripts' },
    { id: uid('s'), guest: 'Shreyas Doshi', title: 'Product sense and prioritisation', episode: "Lenny's Podcast", snippet: 'starting from the user’s job rather than the feature backlog', url: 'https://github.com/ChatPRD/lennys-podcast-transcripts' },
  ]

  const artifacts = []
  if (wantsEssay) {
    artifacts.push({
      id: uid('art'),
      type: 'markdown',
      title: 'Essay: Build the loop, not the funnel',
      content:
        "# Build the loop, not the funnel\n\n" +
        "Most teams inherit a funnel and spend years trying to make it less leaky. The teams that actually compound do something different: they build a loop.\n\n" +
        "## The trap of linear thinking\n\n" +
        "A funnel is a line. You pour traffic in the top and measure what survives to the bottom. Every improvement is additive and every channel eventually saturates.\n\n" +
        "## What a loop changes\n\n" +
        "A loop makes each new user *produce* the next one. Value created by one cohort becomes acquisition for the next.\n\n" +
        "- **Shorter is better than bigger.** A loop that turns in days beats one that turns in months.\n" +
        "- **Reliability compounds.** A loop that works 60% of the time is a different business than one that works 20%.\n\n" +
        "## The takeaway\n\n" +
        "Before you buy another channel, ask what your product does *for the next user* every time someone gets value. That's the loop — and it's the only growth that compounds.\n\n" +
        "> Note: this is a shortened sample. The production Ship 30 skill outputs ~1,250 words grounded in the retrieved transcripts.",
    })
  }
  if (wantsHtml && !wantsEssay) {
    artifacts.push({
      id: uid('art'),
      type: 'html',
      title: 'Growth metrics one-pager',
      content:
        '<div style="font-family: ui-sans-serif, system-ui; max-width: 560px; margin: 0 auto; padding: 28px;">' +
        '<h1 style="font-family: Georgia, serif; font-size: 26px; margin: 0 0 4px; color:#0F3040;">North-star metrics</h1>' +
        '<p style="color:#464858; margin: 0 0 20px;">A starter scorecard for a PLG product.</p>' +
        '<table style="width:100%; border-collapse: collapse; font-size:14px;">' +
        '<thead><tr style="text-align:left; border-bottom:2px solid #D99B7F;">' +
        '<th style="padding:8px 6px;">Metric</th><th style="padding:8px 6px;">Why it matters</th></tr></thead>' +
        '<tbody>' +
        '<tr style="border-bottom:1px solid #E6D5CD;"><td style="padding:8px 6px; font-weight:600;">Activation rate</td><td style="padding:8px 6px; color:#464858;">Share of sign-ups that reach first value.</td></tr>' +
        '<tr style="border-bottom:1px solid #E6D5CD;"><td style="padding:8px 6px; font-weight:600;">Week-4 retention</td><td style="padding:8px 6px; color:#464858;">Does the curve flatten or decay?</td></tr>' +
        '<tr><td style="padding:8px 6px; font-weight:600;">Loop cycle time</td><td style="padding:8px 6px; color:#464858;">How fast one user creates the next.</td></tr>' +
        '</tbody></table></div>',
    })
  }

  return { text, sources, artifacts }
}

// ---- the adapter -----------------------------------------------------------
export const mockApi = {
  async getHealth() {
    await sleep(80)
    return { status: 'ok', db: 'mock', ollama: 'mock' }
  },

  async getConfig() {
    await sleep(60)
    return { activeProviderId, providers }
  },

  async setProvider(providerId) {
    await sleep(120)
    if (providers.some((p) => p.id === providerId)) activeProviderId = providerId
    return { activeProviderId, providers }
  },

  async listSessions() {
    await sleep(80)
    return [...store.sessions].sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''))
  },

  async getMessages(sessionId) {
    await sleep(80)
    return [...(store.messages[sessionId] || [])]
  },

  async deleteSession(sessionId) {
    await sleep(80)
    store.sessions = store.sessions.filter((s) => s.id !== sessionId)
    delete store.messages[sessionId]
  },

  sendMessageStream({ sessionId, content, providerId }, handlers) {
    let cancelled = false
    const timers = []
    const wait = (ms) =>
      new Promise((resolve) => {
        const t = setTimeout(resolve, ms)
        timers.push(t)
      })

    ;(async () => {
      // Create a session lazily on first message.
      let sid = sessionId
      if (!sid) {
        const title = content.length > 48 ? content.slice(0, 47) + '…' : content
        const session = { id: uid('sess'), title, createdAt: nowIso(), updatedAt: nowIso() }
        store.sessions.unshift(session)
        store.messages[session.id] = []
        sid = session.id
        handlers.onSession?.(session)
      }

      // Persist the user message.
      store.messages[sid].push({ id: uid('m'), role: 'user', content, sources: [], artifacts: [], createdAt: nowIso() })

      const { text, sources, artifacts } = buildReply(content)

      await wait(450) // "thinking"
      if (cancelled) return

      // Stream text word by word.
      const words = text.split(/(\s+)/)
      let acc = ''
      for (const w of words) {
        if (cancelled) return
        acc += w
        handlers.onDelta?.(w)
        await wait(18)
      }

      await wait(200)
      if (cancelled) return
      handlers.onSources?.(sources)

      for (const a of artifacts) {
        if (cancelled) return
        await wait(250)
        handlers.onArtifact?.(a)
      }

      const messageId = uid('m')
      store.messages[sid].push({ id: messageId, role: 'assistant', content: acc, sources, artifacts, createdAt: nowIso() })
      const s = store.sessions.find((x) => x.id === sid)
      if (s) s.updatedAt = nowIso()

      await wait(60)
      if (cancelled) return
      handlers.onDone?.(messageId)
    })()

    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  },
}
