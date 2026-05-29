import { useEffect, useState } from "react";
import { api } from "../api";
import { useChatStream } from "../hooks/useChatStream";
import type { AppConfig, Message } from "../types";
import Composer from "./Composer";
import MessageList from "./MessageList";

interface Props {
  conversationId: number;
  config: AppConfig;
  useTools: boolean;
  setUseTools: (v: boolean) => void;
  onConversationUpdated: () => void;
  setSpeaking: (b: boolean) => void;
}

export default function ChatView({
  conversationId,
  config,
  useTools,
  setUseTools,
  onConversationUpdated,
  setSpeaking,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const chat = useChatStream();

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .getConversation(conversationId)
      .then((d) => {
        if (active) {
          setMessages(d.messages);
          setLoading(false);
        }
      })
      .catch(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [conversationId]);

  // AIの発話状態を銀河アニメーションへ伝える
  useEffect(() => {
    setSpeaking(chat.isStreaming);
    return () => setSpeaking(false);
  }, [chat.isStreaming, setSpeaking]);

  function handleSend(content: string) {
    const tempId = -Date.now();
    const firstMessage = messages.length === 0;
    setMessages((m) => [
      ...m,
      {
        id: tempId,
        conversation_id: conversationId,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      },
    ]);
    chat.send(conversationId, content, useTools, {
      onDone: (aid, text, sources) => {
        setMessages((m) => [
          ...m,
          {
            id: aid,
            conversation_id: conversationId,
            role: "assistant",
            content: text,
            meta: sources.length ? { sources } : null,
            created_at: new Date().toISOString(),
          },
        ]);
        if (firstMessage) onConversationUpdated();
      },
    });
  }

  const streamingView = chat.isStreaming
    ? {
        text: chat.streamingText,
        toolStatus: chat.toolStatus,
        sources: chat.liveSources,
      }
    : null;
  const isEmpty = !loading && messages.length === 0 && !chat.isStreaming;

  return (
    <div className="chat">
      {!config.llm_enabled && (
        <div className="notice">
          ANTHROPIC_API_KEY が未設定です。backend/.env に設定するとチャットが使えます。
        </div>
      )}
      {chat.error && (
        <div
          className="notice"
          onClick={chat.clearError}
          style={{ cursor: "pointer" }}
        >
          ⚠ {chat.error}（クリックで閉じる）
        </div>
      )}
      {isEmpty ? (
        <div className="empty-state">
          <h1>{config.owner_name} のためのAI</h1>
          <p>なんでも話しかけてください。相談も、調べ物も。</p>
        </div>
      ) : (
        <MessageList messages={messages} streaming={streamingView} />
      )}
      <Composer
        onSend={handleSend}
        disabled={chat.isStreaming || !config.llm_enabled}
        useTools={useTools}
        setUseTools={setUseTools}
        searchEnabled={config.search_enabled}
        transcriptionEnabled={config.transcription_enabled}
      />
    </div>
  );
}
