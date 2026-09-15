import { createAgentSession, AuthStorage, ModelRegistry, DefaultResourceLoader, SessionManager, SettingsManager } from '@mariozechner/pi-coding-agent'

let input = ''
for await (const chunk of process.stdin) input += chunk
const request = JSON.parse(input)
const authStorage = AuthStorage.inMemory()
authStorage.setRuntimeApiKey(request.provider, request.api_key || 'ollama')
const modelRegistry = ModelRegistry.inMemory(authStorage)
modelRegistry.registerProvider(request.provider, {
  baseUrl: request.base_url,
  api: request.provider === 'anthropic' ? 'anthropic-messages' : 'openai-completions',
  apiKey: request.api_key || 'ollama',
  models: [{
    id: request.model, name: request.model, reasoning: false, input: ['text'],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: request.provider === 'ollama' ? (request.context_length || 8192) : 128000,
    maxTokens: request.max_tokens,
    ...(request.provider === 'ollama' ? { compat: { supportsDeveloperRole: false, supportsReasoningEffort: false, supportsUsageInStreaming: false, maxTokensField: 'max_tokens' } } : {}),
  }],
})
const settingsManager = SettingsManager.inMemory({ compaction: { enabled: false }, retry: { enabled: false } })
const resourceLoader = new DefaultResourceLoader({
  cwd: process.cwd(), agentDir: process.cwd(), settingsManager,
  noExtensions: true, noSkills: true, noPromptTemplates: true, noThemes: true, noContextFiles: true,
  systemPromptOverride: () => request.system,
})
await resourceLoader.reload()
// Resource reload replaces in-memory settings; reapply these after it completes.
settingsManager.setCompactionEnabled(false)
settingsManager.setRetryEnabled(false)
const sessionManager = SessionManager.inMemory()
for (const message of request.messages.slice(0, -1)) {
  sessionManager.appendMessage(message.role === 'user'
    ? { role: 'user', content: message.content, timestamp: Date.now() }
    : { role: 'assistant', content: [{ type: 'text', text: message.content }], api: request.provider === 'anthropic' ? 'anthropic-messages' : 'openai-completions', provider: request.provider, model: request.model, stopReason: 'stop', timestamp: Date.now(), usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } } })
}
const { session } = await createAgentSession({
  authStorage, modelRegistry, model: modelRegistry.find(request.provider, request.model),
  tools: [], thinkingLevel: 'off', resourceLoader, sessionManager, settingsManager,
})
const stream = session.agent.streamFn
session.agent.streamFn = (model, context, options) => stream(model, context, { ...options, maxTokens: request.max_tokens, temperature: request.temperature ?? 0.2 })
// Enforce the limit on the final provider payload as well as stream options.
session.agent.onPayload = payload => ({
  ...payload,
  temperature: request.temperature ?? 0.2,
  ...('max_completion_tokens' in payload
    ? { max_completion_tokens: request.max_tokens }
    : { max_tokens: request.max_tokens }),
})
if (request.stream) {
  session.subscribe(event => {
    if (event.type === 'message_update' && event.assistantMessageEvent.type === 'text_delta') {
      process.stdout.write(JSON.stringify({ type: 'delta', text: event.assistantMessageEvent.delta }) + '\n')
    }
  })
}
try {
  await session.prompt(request.messages.at(-1).content)
  const reply = session.agent.state.messages.filter(m => m.role === 'assistant').at(-1)
  if (!reply || reply.stopReason === 'error' || reply.stopReason === 'aborted') throw new Error(reply?.errorMessage || 'Pi agent did not complete')
  const text = reply.content.filter(c => c.type === 'text').map(c => c.text).join('')
  if (!text) throw new Error('Pi agent returned an empty answer')
  process.stdout.write(JSON.stringify({ text, provider: request.provider, model: request.model }) + '\n')
} finally {
  session.dispose()
}
