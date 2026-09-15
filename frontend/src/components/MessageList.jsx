import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble.jsx'

export default function MessageList({ messages, onOpenArtifact }) {
  const bottomRef = useRef(null)
  const last = messages[messages.length - 1]
  // Re-scroll as new messages arrive and as the streaming reply grows.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages.length, last?.content, last?.artifacts?.length])

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} onOpenArtifact={onOpenArtifact} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
