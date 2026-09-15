export default function TypingIndicator({ label = 'Assistant is thinking' }) {
  return (
    <div className="flex items-center gap-1 py-1" aria-label={label} role="status">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-ink-soft animate-blink"
          style={{ animationDelay: `${i * 0.18}s` }}
        />
      ))}
      <span className="ml-2 text-xs text-muted">{label}</span>
    </div>
  )
}
