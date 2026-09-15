import { BookOpen } from 'lucide-react'

// The one deliberately bold, on-theme flourish: grounded citations rendered as
// highlighted transcript snippets. Reinforces that answers come from Lenny's
// transcripts, and satisfies the grounding/traceability requirement.
export default function Sources({ sources }) {
  if (!sources || sources.length === 0) return null
  return (
    <section className="mt-4 border-t border-line pt-3" aria-label="Sources">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted">
        <BookOpen size={13} />
        {sources.length} retrieved source{sources.length > 1 ? 's' : ''}
      </div>
      <ul className="space-y-2">
        {sources.map((s, index) => (
          <li key={s.id} className="text-sm">
            <div className="flex flex-wrap items-baseline gap-x-1.5">
              <span className="font-medium text-ink">[{index + 1}] {s.guest}</span>
              {s.title && <span className="text-ink-soft">— {s.title}</span>}
            </div>
            {s.snippet && (
              <p className="mt-0.5 text-ink-soft">
                <span className="highlight-mark">{s.snippet}</span>
              </p>
            )}
            {s.url && (
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-0.5 inline-block text-xs text-ink underline decoration-accent-strong underline-offset-2"
              >
                View source
              </a>
            )}
            {s.source_url && (
              <a href={s.source_url} target="_blank" rel="noopener noreferrer" className="ml-3 text-xs text-ink underline decoration-accent-strong underline-offset-2">Read transcript</a>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
