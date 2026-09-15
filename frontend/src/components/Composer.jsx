import { useEffect, useRef, useState } from 'react'
import { Send, Square, CornerDownLeft } from 'lucide-react'
import clsx from 'clsx'

export default function Composer({ onSend, isStreaming, onStop }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  // Auto-grow the textarea up to a cap.
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }, [value])

  const submit = () => {
    const v = value.trim()
    if (!v || isStreaming) return
    onSend(v)
    setValue('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-line bg-paper/80 backdrop-blur">
      <div className="mx-auto w-full max-w-3xl px-4 py-3">
        <div className="flex items-end gap-2 rounded-lg border border-line bg-surface p-2 transition-colors focus-within:border-accent">
          <label htmlFor="composer" className="sr-only">
            Message the assistant
          </label>
          <textarea
            id="composer"
            ref={ref}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about product, growth, or request an essay…"
            className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] leading-relaxed text-ink outline-none placeholder:text-muted"
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={onStop}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-ink text-paper transition-colors hover:bg-ink-soft"
              aria-label="Stop generating"
            >
              <Square size={15} fill="currentColor" />
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={!value.trim()}
              className={clsx(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-md transition-colors',
                value.trim()
                  ? 'bg-accent text-on-accent hover:bg-accent-strong hover:text-ink'
                  : 'bg-line text-muted'
              )}
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          )}
        </div>
        <p className="mt-1.5 flex items-center gap-1 px-1 text-[11px] text-muted">
          <CornerDownLeft size={11} /> Enter to send · Shift + Enter for a new line
        </p>
      </div>
    </div>
  )
}
