import { useCallback, useRef, useState } from "react";

/** マイク録音フック。stop() は録音された Blob を返す（無音/失敗時は null）。 */
export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const resolveRef = useRef<((b: Blob | null) => void) | null>(null);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: mr.mimeType || "audio/webm",
        });
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        resolveRef.current?.(blob.size ? blob : null);
        resolveRef.current = null;
      };
      recorderRef.current = mr;
      mr.start();
      setIsRecording(true);
    } catch (e) {
      setError(
        "マイクにアクセスできません: " +
          (e instanceof Error ? e.message : String(e))
      );
      setIsRecording(false);
    }
  }, []);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mr = recorderRef.current;
      if (!mr || mr.state === "inactive") {
        resolve(null);
        return;
      }
      resolveRef.current = resolve;
      mr.stop();
      setIsRecording(false);
    });
  }, []);

  return { isRecording, error, start, stop };
}
