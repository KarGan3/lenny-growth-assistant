import { Menu, AlertCircle, X } from 'lucide-react'
import MessageList from './MessageList.jsx'
import EmptyState from './EmptyState.jsx'
import Composer from './Composer.jsx'

export default function ChatPanel({ chat, onOpenArtifact, onOpenSidebar }) {
  const empty = chat.messages.length === 0 && !chat.loadingThread

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      {/* Mobile-only top bar; on desktop the sidebar carries identity. */}
      <header className="flex items-center gap-2 border-b border-line px-3 py-2.5 lg:hidden">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="rounded-lg p-2 text-ink-soft hover:bg-paper"
          aria-label="Open menu"
        >
          <Menu size={18} />
        </button>
        <span className="font-serif text-lg text-ink">
          Lenny<span className="text-accent">.</span>
        </span>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {empty ? (
          <EmptyState onPrompt={chat.sendMessage} />
        ) : (
          <MessageList messages={chat.messages} onOpenArtifact={onOpenArtifact} />
        )}
      </div>

      {chat.error && (
        <div className="mx-auto w-full max-w-3xl px-4">
          <div className="mb-2 flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span className="flex-1">{chat.error}</span>
            <button type="button" onClick={chat.dismissError} aria-label="Dismiss error">
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      <Composer onSend={chat.sendMessage} isStreaming={chat.isStreaming} onStop={chat.stop} />
    </div>
  )
}
