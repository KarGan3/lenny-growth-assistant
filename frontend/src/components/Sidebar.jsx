import { Plus, X } from 'lucide-react'
import SessionList from './SessionList.jsx'
import ProviderToggle from './ProviderToggle.jsx'
import { config } from '../config.js'

function Wordmark() {
  return (
    <div className="leading-none">
      <div className="font-serif text-xl font-medium text-ink">
        Lenny<span className="text-accent">.</span>
      </div>
      <div className="mt-1 text-xs text-muted">Growth Assistant</div>
    </div>
  )
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onDelete,
  providers,
  activeProvider,
  onSelectProvider,
  onClose,
}) {
  return (
    <div className="flex h-full flex-col bg-accent-wash/10">
      <div className="flex items-center justify-between px-4 pb-3 pt-4">
        <Wordmark />
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-muted hover:bg-paper lg:hidden"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <div className="px-3">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2.5 text-sm font-medium text-ink transition-colors hover:border-accent hover:bg-accent-wash/25"
        >
          <Plus size={16} className="text-accent" />
          New chat
        </button>
      </div>

      <nav className="mt-4 min-h-0 flex-1 overflow-y-auto px-2" aria-label="Chat history">
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      </nav>

      <div className="space-y-2 border-t border-line px-3 py-3">
        <ProviderToggle providers={providers} activeProvider={activeProvider} onSelect={onSelectProvider} />
        {config.useMock && (
          <p className="px-1 text-[11px] leading-tight text-muted">
            Running on mock data. Set <code className="font-mono">VITE_USE_MOCK=false</code> to use the API.
          </p>
        )}
      </div>
    </div>
  )
}
