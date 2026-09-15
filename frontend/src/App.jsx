import { useCallback, useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import ArtifactViewer from './components/ArtifactViewer.jsx'
import ArtifactBoundary from './components/ArtifactBoundary.jsx'
import { useChat } from './hooks/useChat.js'
import { useMediaQuery } from './hooks/useMediaQuery.js'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [openArtifact, setOpenArtifact] = useState(null)
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  // New artifacts auto-open the viewer as they stream in.
  const chat = useChat({ onArtifact: setOpenArtifact })

  const handleNewChat = useCallback(() => {
    chat.newChat()
    setOpenArtifact(null)
    setSidebarOpen(false)
  }, [chat])

  const handleSelect = useCallback(
    (id) => {
      chat.selectSession(id)
      setOpenArtifact(null)
      setSidebarOpen(false)
    },
    [chat]
  )

  const sidebar = (
    <Sidebar
      sessions={chat.sessions}
      activeSessionId={chat.activeSessionId}
      onSelect={handleSelect}
      onNewChat={handleNewChat}
      onDelete={chat.deleteSession}
      providers={chat.providers}
      activeProvider={chat.activeProvider}
      onSelectProvider={chat.setProvider}
      onClose={() => setSidebarOpen(false)}
    />
  )

  return (
    <div className="flex h-screen overflow-hidden bg-paper text-ink">
      {/* Desktop sidebar */}
      <aside className="hidden w-72 shrink-0 border-r border-line lg:block">{sidebar}</aside>

      {/* Mobile sidebar drawer */}
      {sidebarOpen && !isDesktop && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
          <div className="absolute left-0 top-0 h-full w-72 max-w-[80%] border-r border-line shadow-xl">
            {sidebar}
          </div>
        </div>
      )}

      {/* Main area: chat + (desktop) artifact pane */}
      <div className="flex min-w-0 flex-1">
        <ChatPanel
          chat={chat}
          onOpenArtifact={setOpenArtifact}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        {openArtifact && isDesktop && (
          <aside className="w-[440px] shrink-0 animate-slide-in border-l border-line xl:w-[520px]">
            <ArtifactBoundary key={openArtifact.id + openArtifact.title} onClose={() => setOpenArtifact(null)}>
              <ArtifactViewer artifact={openArtifact} onClose={() => setOpenArtifact(null)} />
            </ArtifactBoundary>
          </aside>
        )}
      </div>

      {/* Mobile artifact overlay */}
      {openArtifact && !isDesktop && (
        <div className="fixed inset-0 z-50 bg-surface">
          <ArtifactBoundary key={openArtifact.id + openArtifact.title} onClose={() => setOpenArtifact(null)}>
              <ArtifactViewer artifact={openArtifact} onClose={() => setOpenArtifact(null)} />
            </ArtifactBoundary>
        </div>
      )}
    </div>
  )
}
