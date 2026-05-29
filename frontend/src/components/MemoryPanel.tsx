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

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [newText, setNewText] = useState("");
  const [adding, setAdding] = useState(false);

  function load() {
    setLoading(true);
    api
      .listMemories()
      .then(setMemories)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  async function add() {
    const t = newText.trim();
    if (!t) return;
    setAdding(true);
    try {
      await api.createMemory(t, "fact", 3);
      setNewText("");
      load();
    } finally {
      setAdding(false);
    }
  }

  async function del(id: number) {
    await api.deleteMemory(id);
    setMemories((m) => m.filter((x) => x.id !== id));
  }

  const grouped = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: memories.filter((m) => m.category === cat),
  })).filter((g) => g.items.length);

  return (
    <div className="panel">
      <div className="panel-inner">
        <h2>記憶</h2>
        <div className="sub">
          あなたについて覚えていること。会話から自動で蓄積され、手動でも追加・削除できます。
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

        {loading ? (
          <div className="sub">
            <span className="spinner" /> 読み込み中…
          </div>
        ) : memories.length === 0 ? (
          <div className="sub">
            まだ記憶はありません。会話すると自動で増えていきます。
          </div>
        ) : (
          grouped.map((g) => (
            <div key={g.cat}>
              <div className="mem-group-title">
                {CATEGORY_LABELS[g.cat] || g.cat}
              </div>
              {g.items.map((m) => (
                <div key={m.id} className="mem-card">
                  <div className="content">{m.content}</div>
                  <div className="stars" title={`重要度 ${m.importance}/5`}>
                    {"★".repeat(m.importance)}
                  </div>
                  <div className="actions">
                    <button onClick={() => del(m.id)} title="削除">
                      削除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
