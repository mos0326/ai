import { useEffect, useState } from "react";
import { api } from "../api";
import type { Memory } from "../types";

const CATEGORY_LABELS: Record<string, string> = {
  goal: "目標",
  project: "プロジェクト",
  relationship: "人間関係",
  preference: "好み",
  fact: "事実",
  other: "その他",
};
const CATEGORY_ORDER = ["goal", "project", "relationship", "preference", "fact", "other"];

interface Draft {
  content: string;
  category: string;
  importance: number;
}

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [newText, setNewText] = useState("");
  const [adding, setAdding] = useState(false);
  const [includeSuperseded, setIncludeSuperseded] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft>({
    content: "",
    category: "fact",
    importance: 3,
  });

  function load(inc: boolean) {
    setLoading(true);
    api
      .listMemories(inc)
      .then(setMemories)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load(includeSuperseded);
  }, [includeSuperseded]);

  async function add() {
    const t = newText.trim();
    if (!t) return;
    setAdding(true);
    try {
      await api.createMemory(t, "fact", 3);
      setNewText("");
      load(includeSuperseded);
    } finally {
      setAdding(false);
    }
  }

  async function del(id: number) {
    await api.deleteMemory(id);
    setMemories((m) => m.filter((x) => x.id !== id));
  }

  function startEdit(m: Memory) {
    setEditingId(m.id);
    setDraft({ content: m.content, category: m.category, importance: m.importance });
  }

  async function saveEdit(id: number) {
    const updated = await api.updateMemory(id, draft);
    setMemories((ms) => ms.map((m) => (m.id === id ? updated : m)));
    setEditingId(null);
  }

  async function setStatus(id: number, status: string) {
    const updated = await api.updateMemory(id, { status });
    if (status !== "active" && !includeSuperseded) {
      setMemories((ms) => ms.filter((m) => m.id !== id));
    } else {
      setMemories((ms) => ms.map((m) => (m.id === id ? updated : m)));
    }
  }

  const active = memories.filter((m) => m.status === "active");
  const superseded = memories.filter((m) => m.status !== "active");
  const grouped = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: active.filter((m) => m.category === cat),
  })).filter((g) => g.items.length);

  function renderCard(m: Memory) {
    if (editingId === m.id) {
      return (
        <div key={m.id} className="mem-card">
          <div className="mem-edit-row">
            <input
              className="edit"
              value={draft.content}
              onChange={(e) => setDraft({ ...draft, content: e.target.value })}
            />
            <select
              value={draft.category}
              onChange={(e) => setDraft({ ...draft, category: e.target.value })}
            >
              {CATEGORY_ORDER.map((c) => (
                <option key={c} value={c}>
                  {CATEGORY_LABELS[c]}
                </option>
              ))}
            </select>
            <select
              value={draft.importance}
              onChange={(e) =>
                setDraft({ ...draft, importance: Number(e.target.value) })
              }
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  ★{n}
                </option>
              ))}
            </select>
          </div>
          <div className="actions">
            <button onClick={() => saveEdit(m.id)} disabled={!draft.content.trim()}>
              保存
            </button>
            <button onClick={() => setEditingId(null)}>取消</button>
          </div>
        </div>
      );
    }
    return (
      <div key={m.id} className={`mem-card ${m.status !== "active" ? "superseded" : ""}`}>
        <div className="content">{m.content}</div>
        <div className="stars" title={`重要度 ${m.importance}/5`}>
          {"★".repeat(m.importance)}
        </div>
        <div className="actions">
          {m.status === "active" ? (
            <>
              <button onClick={() => startEdit(m)} title="編集">
                編集
              </button>
              <button onClick={() => del(m.id)} title="削除">
                削除
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setStatus(m.id, "active")} title="有効化">
                復元
              </button>
              <button onClick={() => del(m.id)} title="削除">
                削除
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-inner">
        <h2>記憶</h2>
        <div className="sub">
          あなたについて覚えていること。会話から自動で蓄積され、手動でも追加・編集・削除できます。
        </div>

        <div className="mem-add">
          <input
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            placeholder="記憶を手動で追加（例: 私は猫を飼っている）"
            onKeyDown={(e) => {
              if (e.key === "Enter") add();
            }}
          />
          <button className="btn" onClick={add} disabled={adding || !newText.trim()}>
            追加
          </button>
        </div>

        <div className="mem-toolbar">
          <label>
            <input
              type="checkbox"
              checked={includeSuperseded}
              onChange={(e) => setIncludeSuperseded(e.target.checked)}
            />
            無効化された記憶も表示
          </label>
        </div>

        {loading ? (
          <div className="sub">
            <span className="spinner" /> 読み込み中…
          </div>
        ) : active.length === 0 && superseded.length === 0 ? (
          <div className="sub">
            まだ記憶はありません。会話すると自動で増えていきます。
          </div>
        ) : (
          <>
            {grouped.map((g) => (
              <div key={g.cat}>
                <div className="mem-group-title">
                  {CATEGORY_LABELS[g.cat] || g.cat}
                </div>
                {g.items.map(renderCard)}
              </div>
            ))}
            {includeSuperseded && superseded.length > 0 && (
              <div>
                <div className="mem-group-title">無効化された記憶</div>
                {superseded.map(renderCard)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
