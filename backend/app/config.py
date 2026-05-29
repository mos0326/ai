"""アプリ設定。環境変数 / .env から読み込む（pydantic-settings）。

注意: アプリは自前の ANTHROPIC_API_KEY で本物の Anthropic API を叩きます。
実行環境側の ANTHROPIC_BASE_URL（Claude Code のプロキシ等）を拾わないよう、
base_url は設定項目として公開していません。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- アプリ / ユーザー ---
    app_name: str = "Personal AI"
    owner_name: str = "あなた"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- データベース ---
    database_url: str = "sqlite:///./personal_ai.db"

    # --- Anthropic (LLM) ---
    anthropic_api_key: str | None = None
    chat_model: str = "claude-sonnet-4-6"
    extraction_model: str = "claude-haiku-4-5-20251001"
    research_model: str = "claude-sonnet-4-6"
    max_tokens: int = 2048

    # --- 埋め込み ---
    embedding_provider: str = "auto"  # auto | openai | voyage | local
    openai_api_key: str | None = None
    voyage_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    voyage_embedding_model: str = "voyage-3"
    local_embedding_dim: int = 384
    # pgvector 使用時の固定次元。プロバイダの出力次元に合わせる
    # （openai text-embedding-3-small=1536 / voyage-3=1024 / local=local_embedding_dim）
    embedding_dim: int = 1536

    # --- 検索 / リサーチ ---
    search_provider: str = "tavily"  # tavily | brave | none
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    research_max_results: int = 6
    research_fetch_pages: int = 4

    # --- 文字起こし ---
    transcription_provider: str = "openai"  # openai | faster-whisper
    whisper_model: str = "whisper-1"
    faster_whisper_model: str = "base"

    # --- 記憶システム ---
    memory_top_k: int = 6
    memory_min_similarity: float = 0.25
    memory_extraction_enabled: bool = True

    # --- 便利プロパティ ---
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def resolved_embedding_provider(self) -> str:
        """auto を実際のプロバイダ名に解決する。"""
        if self.embedding_provider != "auto":
            return self.embedding_provider
        if self.openai_api_key:
            return "openai"
        if self.voyage_api_key:
            return "voyage"
        return "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
