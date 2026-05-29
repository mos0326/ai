import { useCallback, useState } from "react";
import { api } from "../api";
import type { Source } from "../types";

export interface MemoryAdded {
  id: number;
  content: string;
  category: string;
}

export interface ChatCallbacks {
  onStart?: (userMessageId: number) => void;
  onDone?: (assistantMessageId: number, text: string, sources: Source[]) => void;
  onMemory?: (added: MemoryAdded[]) => void;
}

interface State {
  isStreaming: boolean;
  streamingText: string;
  toolStatus: string | null;
  liveSources: Source[];
  error: string | null;
}

const INITIAL: State = {
  isStreaming: false,
  streamingText: "",
  toolStatus: null,
  liveSources: [],
  error: null,
};

function toolLabel(name: string): string {
  if (name === "web_search") return "Web検索中…";
  if (name === "fetch_url") return "ページを読み込み中…";
  return "考え中…";
}

/** SSE チャットストリームを処理するフック。 */
export function useChatStream() {
  const [state, setState] = useState<State>(INITIAL);

  const send = useCallback(
    async (
      conversationId: number,
      content: string,
      useTools: boolean,
      cb: ChatCallbacks
    ) => {
      setState({ ...INITIAL, isStreaming: true });
      let text = "";
      let sources: Source[] = [];

      try {
        const resp = await fetch(api.chatStreamUrl(conversationId), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content, use_tools: useTools }),
        });
        if (!resp.ok || !resp.body) {
          throw new Error("サーバーに接続できませんでした");
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const dataLine = rawEvent
              .split("\n")
              .find((l) => l.startsWith("data:"));
            if (!dataLine) continue;
            let ev: any;
            try {
              ev = JSON.parse(dataLine.slice(5).trim());
            } catch {
              continue;
            }

            switch (ev.type) {
              case "start":
                cb.onStart?.(ev.user_message_id);
                break;
              case "delta":
                text += ev.text;
                setState((s) => ({ ...s, streamingText: text }));
                break;
              case "tool":
                if (ev.phase === "done") {
                  setState((s) => ({ ...s, toolStatus: null }));
                } else {
                  setState((s) => ({ ...s, toolStatus: toolLabel(ev.name) }));
                }
                break;
              case "sources":
                sources = ev.sources || [];
                setState((s) => ({ ...s, liveSources: sources }));
                break;
              case "done":
                cb.onDone?.(ev.assistant_message_id, text, sources);
                setState((s) => ({
                  ...s,
                  isStreaming: false,
                  streamingText: "",
                  toolStatus: null,
                }));
                break;
              case "memory":
                cb.onMemory?.(ev.added || []);
                break;
              case "error":
                setState((s) => ({ ...s, error: ev.message, isStreaming: false }));
                break;
            }
          }
        }
      } catch (e) {
        setState((s) => ({
          ...s,
          error: e instanceof Error ? e.message : String(e),
        }));
      } finally {
        setState((s) => ({
          ...s,
          isStreaming: false,
          streamingText: "",
          toolStatus: null,
        }));
      }
    },
    []
  );

  const clearError = useCallback(
    () => setState((s) => ({ ...s, error: null })),
    []
  );

  return { ...state, send, clearError };
}
