import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import ChatView from "./components/ChatView";
import GalaxyCanvas from "./components/GalaxyCanvas";
import MemoryPanel from "./components/MemoryPanel";
import ResearchPanel from "./components/ResearchPanel";
import Sidebar from "./components/Sidebar";
import type { View } from "./components/Sidebar";
import type { AppConfig, Conversation } from "./types";

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [view, setView] = useState<View>("chat");
  const [speaking, setSpeaking] = useState(false);
  const [useTools, setUseTools] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const refreshConversations = useCallback(async () => {
    const list = await api.listConversations();
    setConversations(list);
    return list;
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const cfg = await api.getConfig();
        setConfig(cfg);
        setUseTools(cfg.search_enabled);
        await api.getMe();
        let list = await refreshConversations();
        if (list.length === 0) {
          const c = await api.createConversation();
          list = [c];
          setConversations(list);
        }
        setActiveId(list[0].id);
      } catch (e) {
        console.error("初期化に失敗:", e);
      }
    })();
  }, [refreshConversations]);

  const newConversation = useCallback(async () => {
    const c = await api.createConversation();
    await refreshConversations();
    setActiveId(c.id);
    setView("chat");
    setSidebarOpen(false);
  }, [refreshConversations]);

  const selectConversation = useCallback((id: number) => {
    setActiveId(id);
    setView("chat");
    setSidebarOpen(false);
  }, []);

  const deleteConversation = useCallback(
    async (id: number) => {
      await api.deleteConversation(id);
      const list = await refreshConversations();
      if (activeId === id) {
        if (list.length) {
          setActiveId(list[0].id);
        } else {
          const c = await api.createConversation();
          setConversations([c]);
          setActiveId(c.id);
        }
      }
    },
    [activeId, refreshConversations]
  );

  return (
    <>
      <GalaxyCanvas speaking={speaking} />
      <div className="app">
        <button
          className="icon-btn menu-toggle"
          onClick={() => setSidebarOpen((o) => !o)}
        >
          ☰
        </button>
        <Sidebar
          conversations={conversations}
          activeId={activeId}
          view={view}
          config={config}
          open={sidebarOpen}
          onSelect={selectConversation}
          onNew={newConversation}
          onDelete={deleteConversation}
          setView={(v) => {
            setView(v);
            setSidebarOpen(false);
          }}
        />
        <main className="main">
          {!config && (
            <div className="empty-state">
              <span className="spinner" />
            </div>
          )}
          {view === "chat" && config && activeId != null && (
            <ChatView
              key={activeId}
              conversationId={activeId}
              config={config}
              useTools={useTools}
              setUseTools={setUseTools}
              onConversationUpdated={refreshConversations}
              setSpeaking={setSpeaking}
            />
          )}
          {view === "memories" && config && <MemoryPanel />}
          {view === "research" && config && (
            <ResearchPanel searchEnabled={config.search_enabled} />
          )}
        </main>
      </div>
    </>
  );
}
