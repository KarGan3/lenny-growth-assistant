import { useMemo, useState } from 'react'
import { X, Copy, Download, Eye, Code2, Check, ShieldCheck } from 'lucide-react'
import clsx from 'clsx'
import Markdown from '../lib/Markdown.jsx'
import { sanitizeArtifactHtml, buildSandboxSrcDoc } from '../lib/sanitize.js'

function slug(s) {
  return (s || 'artifact').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

export default function ArtifactViewer({ artifact, onClose }) {
  const [view, setView] = useState('preview')
  const [copied, setCopied] = useState(false)
  const isHtml = artifact.type === 'html'

  // Sanitize once per artifact; the iframe gets a locked-down document.
  const srcDoc = useMemo(
    () => (isHtml ? buildSandboxSrcDoc(sanitizeArtifactHtml(artifact.content)) : ''),
    [artifact.content, isHtml]
  )

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard blocked; no-op */
    }
  }

  const download = () => {
    const ext = isHtml ? 'html' : 'md'
    const blob = new Blob([artifact.content], {
      type: isHtml ? 'text/html' : 'text/markdown',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${slug(artifact.title)}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex h-full flex-col bg-surface">
      <header className="flex items-center gap-2 border-b border-line px-3 py-2.5">
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium text-ink">{artifact.title}</div>
          <div className="flex items-center gap-1.5 text-xs text-muted">
            {isHtml ? (
              <>
                <ShieldCheck size={12} className="text-local" />
                Sandboxed HTML · no scripts, no network
              </>
            ) : (
              'Markdown document'
            )}
          </div>
        </div>

        {/* Preview / Code toggle */}
        <div className="flex rounded-md border border-line p-0.5" role="tablist" aria-label="Artifact view">
          {[
            { id: 'preview', label: 'Preview', Icon: Eye },
            { id: 'code', label: 'Code', Icon: Code2 },
          ].map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={view === id}
              onClick={() => setView(id)}
              className={clsx(
                'flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors',
                view === id ? 'bg-accent-wash text-ink' : 'text-muted hover:text-ink'
              )}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={copy}
          className="rounded-md p-1.5 text-muted hover:bg-paper hover:text-ink"
          aria-label="Copy source"
        >
          {copied ? <Check size={16} className="text-local" /> : <Copy size={16} />}
        </button>
        <button
          type="button"
          onClick={download}
          className="rounded-md p-1.5 text-muted hover:bg-paper hover:text-ink"
          aria-label="Download artifact"
        >
          <Download size={16} />
        </button>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1.5 text-muted hover:bg-paper hover:text-ink"
          aria-label="Close artifact"
        >
          <X size={17} />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-auto">
        {view === 'code' ? (
          <pre className="overflow-auto p-4 font-mono text-[12.5px] leading-relaxed text-ink-soft">
            {artifact.content}
          </pre>
        ) : isHtml ? (
          <iframe
            title={artifact.title}
            sandbox=""
            srcDoc={srcDoc}
            className="h-full w-full border-0 bg-white"
          />
        ) : (
          <div className="p-5">
            <Markdown>{artifact.content}</Markdown>
          </div>
        )}
      </div>
    </div>
  )
}
