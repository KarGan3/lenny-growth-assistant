import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// react-markdown does NOT render raw embedded HTML unless you add rehype-raw —
// we deliberately don't, so chat + markdown artifacts are safe by construction.
// (Untrusted *HTML* artifacts go through the sanitize + sandbox path instead.)

const components = {
  a: (props) => <a {...props} target="_blank" rel="noopener noreferrer" />,
  table: (props) => (
    <div className="my-4 overflow-x-auto">
      <table {...props} className="w-full border-collapse text-sm" />
    </div>
  ),
  th: (props) => <th {...props} className="border-b-2 border-accent px-3 py-2 text-left font-semibold" />,
  td: (props) => <td {...props} className="border-b border-line px-3 py-2 align-top" />,
  code: ({ inline, className, children, ...props }) =>
    inline ? (
      <code className="rounded bg-line/60 px-1.5 py-0.5 font-mono text-[0.85em]" {...props}>
        {children}
      </code>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    ),
  pre: (props) => (
    <pre className="my-4 overflow-x-auto rounded-lg border border-line bg-paper p-4 font-mono text-[0.85em]" {...props} />
  ),
}

export default function Markdown({ children, className = '' }) {
  return (
    <div className={`prose prose-sm max-w-measure prose-headings:font-serif ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children || ''}
      </ReactMarkdown>
    </div>
  )
}
