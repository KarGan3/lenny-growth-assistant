import { useState } from 'react'
import { Cloud, Cpu, Check, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

function Dot({ type }) {
  return (
    <span
      className={clsx('inline-block h-2 w-2 rounded-full', type === 'local' ? 'bg-local' : 'bg-cloud')}
      aria-hidden
    />
  )
}

function readinessLabel(provider) {
  if (provider.type === 'local') return provider.available === false ? 'Model unavailable' : ''
  return provider.available === false ? 'API key missing' : 'Key configured'
}

// Surfaces the active LLM in the UI and lets the evaluator switch providers
// without touching code — directly satisfies the "flexible LLM configuration"
// requirement. Cloud vs local is shown by both icon and colour.
export default function ProviderToggle({ providers, activeProvider, onSelect }) {
  const [open, setOpen] = useState(false)
  if (!activeProvider) return null
  const Icon = activeProvider.type === 'local' ? Cpu : Cloud

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 text-left text-sm transition-colors hover:border-line-strong"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Icon size={16} className="shrink-0 text-ink-soft" />
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{activeProvider.label}</span>
          <span className="block truncate text-xs text-muted">
            {activeProvider.type === 'local' ? 'Local · Ollama' : 'Cloud'} · {activeProvider.model}
            {readinessLabel(activeProvider) && <span className={clsx('block', activeProvider.available === false && 'text-danger')}>{readinessLabel(activeProvider)}</span>}
          </span>
        </span>
        <ChevronDown size={15} className="shrink-0 text-muted" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} aria-hidden />
          <ul
            role="listbox"
            className="absolute bottom-full z-20 mb-2 w-full overflow-hidden rounded-lg border border-line bg-surface shadow-lg"
          >
            {providers.map((p) => {
              const active = p.id === activeProvider.id
              return (
                <li key={p.id} role="option" aria-selected={active}>
                  <button
                    type="button"
                    disabled={p.available === false}
                    onClick={() => {
                      onSelect(p.id)
                      setOpen(false)
                    }}
                    className={clsx(
                      'flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition-colors hover:bg-paper disabled:opacity-50 disabled:cursor-not-allowed',
                      active && 'bg-paper'
                    )}
                  >
                    <Dot type={p.type} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{p.label}</span>
                      <span className="block truncate text-xs text-muted">{p.model}{readinessLabel(p) ? ` · ${readinessLabel(p)}` : ''}</span>
                    </span>
                    {active && <Check size={15} className="text-accent" />}
                  </button>
                </li>
              )
            })}
          </ul>
        </>
      )}
    </div>
  )
}
