import { ArrowUpRight } from 'lucide-react'

// The "hero": a new chat opens on the most characteristic moment — a focused
// prompt to interrogate a corpus of product/growth wisdom. Two of the starter
// prompts deliberately exercise the artifact viewer (an essay and an HTML card).
const STARTERS = [
  'How do I know when I have product-market fit?',
  'What separates growth loops from a funnel?',
  'Draft a Ship 30 for 30 essay on user activation',
  'Make an HTML one-pager of north-star metrics',
]

export default function EmptyState({ onPrompt }) {
  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-6 text-center">
      <h1 className="font-serif text-3xl font-medium leading-tight text-ink sm:text-4xl">
        Ask Lenny’s Podcast anything
        <span className="text-accent">.</span>
      </h1>
      <p className="mt-3 max-w-md text-[15px] text-ink-soft">
        Grounded answers, reusable essays, and rendered artifacts — drawn from{' '}
        <span className="highlight-mark">indexed episode transcripts</span> of product and growth
        conversations.
      </p>

      <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
        {STARTERS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPrompt(s)}
            className="group flex items-center justify-between gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-left text-sm text-ink-soft transition-colors hover:border-accent hover:bg-accent-wash/30 hover:text-ink"
          >
            <span>{s}</span>
            <ArrowUpRight
              size={16}
              className="shrink-0 text-muted transition-colors group-hover:text-accent"
            />
          </button>
        ))}
      </div>
    </div>
  )
}
