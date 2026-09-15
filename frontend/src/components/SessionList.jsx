import { MessageSquare, Trash2 } from 'lucide-react'
import clsx from 'clsx'

export default function SessionList({ sessions, activeSessionId, onSelect, onDelete }) {
  if (sessions.length === 0) {
    return <p className="px-3 py-6 text-sm text-muted">No chats yet. Start one above.</p>
  }
  return (
    <ul className="space-y-0.5">
      {sessions.map((s) => {
        const active = s.id === activeSessionId
        return (
          <li key={s.id} className="group relative">
            <button
              type="button"
              onClick={() => onSelect(s.id)}
              data-session-id={s.id}
              aria-current={active ? 'true' : undefined}
              className={clsx(
                'flex w-full items-center gap-2 rounded-lg py-2 pl-3 pr-9 text-left text-sm transition-colors',
                active ? 'bg-accent-wash text-ink' : 'text-ink-soft hover:bg-paper'
              )}
            >
              <MessageSquare size={15} className={clsx('shrink-0', active ? 'text-accent' : 'text-muted')} />
              <span className="truncate">{s.title}</span>
            </button>
            <button
              type="button"
              onClick={() => onDelete(s.id)}
              aria-label={`Delete chat: ${s.title}`}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded p-1.5 text-muted opacity-0 transition-opacity hover:text-danger focus-visible:opacity-100 group-hover:opacity-100"
            >
              <Trash2 size={14} />
            </button>
          </li>
        )
      })}
    </ul>
  )
}
