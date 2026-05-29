import { useRef, useState } from "react";
import { api } from "../api";
import { useRecorder } from "../hooks/useRecorder";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
  useTools: boolean;
  setUseTools: (v: boolean) => void;
  searchEnabled: boolean;
  transcriptionEnabled: boolean;
}

export default function Composer({
  onSend,
  disabled,
  useTools,
  setUseTools,
  searchEnabled,
  transcriptionEnabled,
}: Props) {
  const [text, setText] = useState("");
  const [transcribing, setTranscribing] = useState(false);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const rec = useRecorder();

  function autoGrow() {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }

  function submit() {
    const t = text.trim();
    if (!t || disabled) return;
    onSend(t);
    setText("");
    requestAnimationFrame(() => {
      if (taRef.current) taRef.current.style.height = "auto";
    });
  }

  async function toggleMic() {
    if (rec.isRecording) {
      const blob = await rec.stop();
      if (blob) {
        setTranscribing(true);
        try {
          const { text: transcript } = await api.transcribe(blob);
          setText((prev) => (prev ? prev + " " : "") + transcript);
          requestAnimationFrame(autoGrow);
        } catch (e) {
          alert(
            "文字起こしに失敗しました: " +
              (e instanceof Error ? e.message : String(e))
          );
        } finally {
          setTranscribing(false);
        }
      }
    } else {
      rec.start();
    }
  }

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          ref={taRef}
          value={text}
          rows={1}
          placeholder="メッセージを入力…（Enterで送信 / Shift+Enterで改行）"
          onChange={(e) => {
            setText(e.target.value);
            autoGrow();
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        {transcriptionEnabled && (
          <button
            className={`icon-btn ${rec.isRecording ? "recording" : ""}`}
            onClick={toggleMic}
            disabled={transcribing}
            title={rec.isRecording ? "停止して文字起こし" : "録音開始"}
          >
            {transcribing ? (
              <span className="spinner" />
            ) : rec.isRecording ? (
              "■"
            ) : (
              "🎙"
            )}
          </button>
        )}
        <button
          className="icon-btn send"
          onClick={submit}
          disabled={disabled || !text.trim()}
          title="送信"
        >
          ➤
        </button>
      </div>
      <div className="composer-meta">
        {searchEnabled ? (
          <label className="toggle">
            <input
              type="checkbox"
              checked={useTools}
              onChange={(e) => setUseTools(e.target.checked)}
            />
            Web検索を使う
          </label>
        ) : (
          <span>Web検索: 未設定（TAVILY_API_KEY等）</span>
        )}
        {rec.error && <span className="warn">{rec.error}</span>}
      </div>
    </div>
  );
}
