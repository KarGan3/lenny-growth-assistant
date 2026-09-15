import { FileText, Code2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import Markdown from '../lib/Markdown.jsx'
import Sources from './Sources.jsx'
import TypingIndicator from './TypingIndicator.jsx'

function ArtifactChip({ artifact, onOpen }) {
  const Icon = artifact.type === 'html' ? Code2 : FileText
  return (
    <button
      type="button"
      onClick={() => onOpen(artifact)}
      className="group mt-3 flex w-full max-w-sm items-center gap-3 rounded-lg border border-line bg-surface px-3 py-2.5 text-left transition-colors hover:border-accent hover:bg-accent-wash/30"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent-wash text-ink">
        <Icon size={17} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-ink">{artifact.title}</span>
        <span className="block text-xs text-muted">
          {artifact.type === 'html' ? 'HTML artifact' : 'Markdown document'} · Open in viewer
        </span>
      </span>
    </button>
  )
}

export default function MessageBubble({ message, onOpenArtifact }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-lg rounded-br-sm border border-line bg-surface px-4 py-2.5 text-[15px] text-ink">
          {message.content}
        </div>
      </div>
    )
  }

  const showTyping = message.pending && !message.content

  return (
    <div className="flex gap-3">
      <div
        className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-ink font-serif text-sm text-paper"
        aria-hidden
      >
        L
      </div>
      <div className="min-w-0 flex-1">
        {showTyping ? (
          <TypingIndicator label={message.status || 'Preparing answer…'} />
        ) : (
          <>
            <Markdown className="text-[15px]">{message.content}</Markdown>
            {message.artifacts?.map((a) => (
              <ArtifactChip key={a.id} artifact={a} onOpen={onOpenArtifact} />
            ))}
          </>
        )}
        <Sources sources={message.sources} />
        {message.warnings?.map((warning) => (
          <p key={warning} role="status" className="mt-2 text-sm text-ink-soft">{warning}</p>
        ))}
        {message.error && (
          <div className={clsx('mt-2 flex items-center gap-2 text-sm text-danger')}>
            <AlertCircle size={15} />
            {message.errorMessage || 'This response didn’t finish. Try sending it again.'}
          </div>
        )}
      </div>
    </div>
  )
}
