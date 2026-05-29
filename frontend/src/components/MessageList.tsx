import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message, Source } from "../types";

interface StreamingView {
  text: string;
  toolStatus: string | null;
  sources: Source[];
}

interface Props {
  messages: Message[];
  streaming: StreamingView | null;
}

const mdComponents = {
  a: ({ node, ...props }: any) => (
    <a {...props} target="_blank" rel="noreferrer" />
  ),
};

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function SourceChips({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null;
  return (
    <div className="sources">
      {sources.map((s) => (
        <a
          key={s.n}
          className="source-chip"
          href={s.url}
          target="_blank"
          rel="noreferrer"
          title={s.title}
        >
          <b>[{s.n}]</b>
          {hostname(s.url)}
        </a>
      ))}
    </div>
  );
}

export default function MessageList({ messages, streaming }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streaming?.text, streaming?.toolStatus]);

  return (
    <div className="messages">
      <div className="messages-inner">
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.role}`}>
            {m.role === "user" ? (
              <div className="bubble">{m.content}</div>
            ) : (
              <div>
                <div className="prose">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                    {m.content}
                  </ReactMarkdown>
                </div>
                {m.meta?.sources && <SourceChips sources={m.meta.sources} />}
              </div>
            )}
          </div>
        ))}

        {streaming && (
          <div className="msg assistant">
            <div>
              <div className="prose">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                  {streaming.text}
                </ReactMarkdown>
                <span className="cursor" />
              </div>
              {streaming.toolStatus && (
                <div className="tool-status">
                  <span className="pulse" />
                  {streaming.toolStatus}
                </div>
              )}
              {streaming.sources?.length > 0 && (
                <SourceChips sources={streaming.sources} />
              )}
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
