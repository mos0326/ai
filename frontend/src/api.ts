import type {
  AppConfig,
  Conversation,
  ConversationDetail,
  Memory,
  ResearchResult,
  User,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const j = await resp.json();
      detail = j.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  getConfig: () => http<AppConfig>("/api/config"),
  getMe: () => http<User>("/api/me"),

  listConversations: () => http<Conversation[]>("/api/conversations"),
  createConversation: () =>
    http<Conversation>("/api/conversations", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getConversation: (id: number) =>
    http<ConversationDetail>(`/api/conversations/${id}`),
  renameConversation: (id: number, title: string) =>
    http<Conversation>(`/api/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (id: number) =>
    http<void>(`/api/conversations/${id}`, { method: "DELETE" }),

  listMemories: (includeSuperseded = false) =>
    http<Memory[]>(
      `/api/memories?include_superseded=${includeSuperseded ? "true" : "false"}`
    ),
  createMemory: (content: string, category: string, importance: number) =>
    http<Memory>("/api/memories", {
      method: "POST",
      body: JSON.stringify({ content, category, importance }),
    }),
  updateMemory: (
    id: number,
    patch: Partial<{
      content: string;
      category: string;
      importance: number;
      status: string;
    }>
  ) =>
    http<Memory>(`/api/memories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  deleteMemory: (id: number) =>
    http<void>(`/api/memories/${id}`, { method: "DELETE" }),

  research: (query: string) =>
    http<ResearchResult>("/api/research", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  transcribe: async (blob: Blob): Promise<{ text: string }> => {
    const form = new FormData();
    form.append("file", blob, "audio.webm");
    const resp = await fetch(BASE + "/api/transcribe", {
      method: "POST",
      body: form,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        const j = await resp.json();
        detail = j.detail || detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    return resp.json();
  },

  chatStreamUrl: (cid: number) => BASE + `/api/conversations/${cid}/chat`,
};
