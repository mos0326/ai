export interface User {
  id: number;
  name: string;
  created_at: string;
}

export interface Source {
  n: number;
  title: string;
  url: string;
  snippet?: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  meta?: { sources?: Source[]; model?: string } | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Memory {
  id: number;
  user_id: number;
  content: string;
  category: string;
  importance: number;
  status: string;
  source_message_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface AppConfig {
  app_name: string;
  owner_name: string;
  chat_model: string;
  embedding_provider: string;
  search_enabled: boolean;
  transcription_enabled: boolean;
  llm_enabled: boolean;
}

export interface ResearchResult {
  query: string;
  summary: string;
  sources: Source[];
  images: string[];
}
