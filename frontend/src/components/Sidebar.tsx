import type { AppConfig, Conversation } from "../types";

export type View = "chat" | "memories" | "research";

interface Props {
  conversations: Conversation[];
  activeId: number | null;
  view: View;
  config: AppConfig | null;
  open: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
  setView: (v: View) => void;
}

function StatusDot({ on, label }: { on: boolean; label: string }) {
  return (
    <div>
      <span className={`dot ${on ? "on" : "off"}`} />
      {label}: {on ? "有効" : "未設定"}
    </div>
  );
}

export default function Sidebar({
  conversations,
  activeId,
  view,
  config,
  open,
  onSelect,
  onNew,
  onDelete,
  setView,
}: Props) {
  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-header">
        <div className="brand">
          {config?.app_name || "Personal AI"}
          <small>{config ? `for ${config.owner_name}` : ""}</small>
        </div>
      </div>

      <div className="nav">
        <button
          className={view === "chat" ? "active" : ""}
          onClick={() => setView("chat")}
        >
          対話
        </button>
        <button
          className={view === "memories" ? "active" : ""}
          onClick={() => setView("memories")}
        >
          記憶
        </button>
        <button
          className={view === "research" ? "active" : ""}
          onClick={() => setView("research")}
        >
          調べ物
        </button>
      </div>

      <button className="new-chat" onClick={onNew}>
        ＋ 新しい会話
      </button>

      <div className="conv-list">
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`conv-item ${
              view === "chat" && c.id === activeId ? "active" : ""
            }`}
            onClick={() => onSelect(c.id)}
          >
            <span className="title">{c.title}</span>
            <button
              className="del"
              title="削除"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
            >
              ✕
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <div style={{ padding: "10px", fontSize: 12, color: "var(--text-dim)" }}>
            まだ会話がありません
          </div>
        )}
      </div>

      {config && (
        <div className="sidebar-footer">
          <StatusDot on={config.llm_enabled} label="Claude" />
          <StatusDot on={config.search_enabled} label="検索" />
          <StatusDot on={config.transcription_enabled} label="文字起こし" />
          <div style={{ marginTop: 6, opacity: 0.7 }}>
            記憶: {config.embedding_provider}
          </div>
        </div>
      )}
    </aside>
  );
}
