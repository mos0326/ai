import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "../api";
import type { ResearchResult } from "../types";

const mdComponents = {
  a: ({ node, ...props }: any) => (
    <a {...props} target="_blank" rel="noreferrer" />
  ),
};

export default function ResearchPanel({ searchEnabled }: { searchEnabled: boolean }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const q = query.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.research(q);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-inner">
        <h2>調べ物</h2>
        <div className="sub">Webを横断して調べ、出典付きで要約します。</div>

        {!searchEnabled && (
          <div className="notice">
            検索APIキー（TAVILY_API_KEY 等）が未設定です。設定すると利用できます。
          </div>
        )}

        <div className="research-bar">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="調べたいことを入力…"
            onKeyDown={(e) => {
              if (e.key === "Enter") run();
            }}
          />
          <button className="btn" onClick={run} disabled={loading || !query.trim()}>
            {loading ? <span className="spinner" /> : "調べる"}
          </button>
        </div>

        {error && <div className="notice">⚠ {error}</div>}

        {result && (
          <div>
            <div className="research-summary">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                {result.summary}
              </ReactMarkdown>
            </div>

            {result.images.length > 0 && (
              <div className="research-images">
                {result.images.map((src, i) => (
                  <img key={i} src={src} alt="" loading="lazy" />
                ))}
              </div>
            )}

            {result.sources.length > 0 && (
              <div className="source-list">
                {result.sources.map((s) => (
                  <a
                    key={s.n}
                    className="item"
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <b>[{s.n}]</b>
                    {s.title}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
