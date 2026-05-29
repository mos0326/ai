# Personal AI — パーソナルAIアシスタント

自分専用のパーソナルAIアシスタントWebアプリ。あなたの生活・思考・嗜好を**記憶**し、
日常の相談相手になりつつ、**リサーチ**・**情報収集**・**文字起こし**を得意とするAIエージェント。

中央に脈動する銀河風オーブ。AIが話している間、星とオーブが「ぼわんぼわん」と発光します。

```
┌─────────────┐      SSE / REST       ┌──────────────────────────┐
│  React (Vite)│ ───────────────────▶ │  FastAPI                  │
│  銀河UI       │                       │  ├ chat (streaming+tools) │ ─▶ Anthropic Claude
│  チャット/記憶 │ ◀─────────────────── │  ├ memory (抽出/検索/注入) │ ─▶ 埋め込み(OpenAI/Voyage/local)
│  /リサーチ     │                       │  ├ research (検索→要約)    │ ─▶ Tavily / Brave
└─────────────┘                       │  └ transcribe (Whisper)   │ ─▶ OpenAI / faster-whisper
                                        │     SQLite (+ベクトル検索) │
                                        └──────────────────────────┘
```

## 特長

- **記憶システム（中核）**: 会話を全件保存し、会話から「あなたに関する事実」（嗜好・人間関係・
  進行中のプロジェクト・目標など）を自動抽出。重複・矛盾を解消しながら蓄積し、新しい会話では
  関連する記憶をベクトル類似検索でプロンプトに注入します（RAG的）。
- **ストリーミングチャット**: 記憶を踏まえたパーソナルな対話を SSE でリアルタイム表示。
- **リサーチ**: Web検索 → 複数ソース統合 → 出典付き要約。会話中も Claude が自分で検索ツールを
  呼んで [1][2] 形式で出典を引用します。画像も取得。
- **文字起こし**: マイク録音 or 音声ファイルを Whisper で文字起こし → そのまま会話に投入。
- **プラガブル & キー無しでも起動**: 埋め込み/検索/文字起こしのプロバイダは差し替え可能。
  APIキーが無くてもサーバーは起動し、該当機能だけ無効化（埋め込みは local フォールバック）。

## 技術スタック

| 領域        | 採用                                                        |
| ----------- | ----------------------------------------------------------- |
| Backend     | Python 3.11 / FastAPI / SQLAlchemy 2.0                       |
| Frontend    | React 18 + Vite + TypeScript                                |
| DB          | SQLite（既定）。`DATABASE_URL` で Postgres へ移行可          |
| ベクトル検索 | アプリ内コサイン類似度（numpy）。pgvector へ差し替え可        |
| LLM         | Anthropic Claude（chat / 抽出 / リサーチでモデル分離可）      |
| 埋め込み     | OpenAI（既定）/ Voyage / local フォールバック               |
| 検索        | Tavily（既定）/ Brave                                        |
| 文字起こし   | OpenAI Whisper API（既定）/ faster-whisper（ローカル）       |

## セットアップ

### 1. バックエンド

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 環境変数（すべて任意。未設定でも起動します）
cp ../.env.example .env
#   - ANTHROPIC_API_KEY  … チャット/リサーチ/記憶抽出に必須
#   - OPENAI_API_KEY     … 埋め込み(text-embedding-3-small) と Whisper 文字起こし
#   - TAVILY_API_KEY     … Web検索 / リサーチ
#   - OWNER_NAME         … AIがあなたを呼ぶ名前

./run.sh          # = uvicorn app.main:app --reload --port 8000
```

API は http://localhost:8000 、ドキュメントは http://localhost:8000/docs 。

### 2. フロントエンド

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173 （/api は 8000 へプロキシ）
```

ブラウザで http://localhost:5173 を開く。マイクは HTTPS か localhost で動作します。

## 環境変数

`.env.example` を参照。主なもの:

| 変数                    | 既定                        | 説明                                    |
| ----------------------- | --------------------------- | --------------------------------------- |
| `ANTHROPIC_API_KEY`     | （未設定）                  | Claude。未設定だとチャット不可          |
| `CHAT_MODEL`            | `claude-sonnet-4-6`         | 対話モデル（`claude-opus-4-8` 等に変更可）|
| `EXTRACTION_MODEL`      | `claude-haiku-4-5-...`      | 記憶抽出用（安価・高速）                |
| `EMBEDDING_PROVIDER`    | `auto`                      | `auto`/`openai`/`voyage`/`local`        |
| `OPENAI_API_KEY`        | （未設定）                  | 埋め込み + Whisper                      |
| `SEARCH_PROVIDER`       | `tavily`                    | `tavily`/`brave`                        |
| `TAVILY_API_KEY`        | （未設定）                  | Web検索                                 |
| `TRANSCRIPTION_PROVIDER`| `openai`                    | `openai`/`faster-whisper`               |
| `DATABASE_URL`          | `sqlite:///./personal_ai.db`| Postgres 例は `.env.example` 参照        |
| `MEMORY_TOP_K`          | `6`                         | 注入する記憶の件数                      |

## API 概要

| メソッド | パス                                  | 説明                                  |
| -------- | ------------------------------------- | ------------------------------------- |
| GET      | `/api/health` `/api/config`           | ヘルス / 公開設定・機能の有効状態      |
| GET      | `/api/me`                             | 既定ユーザー（無ければ作成）          |
| GET/POST | `/api/conversations`                  | 会話の一覧 / 作成                     |
| GET/PATCH/DELETE | `/api/conversations/{id}`     | 会話の詳細(メッセージ含む) / 改名 / 削除 |
| POST     | `/api/conversations/{id}/chat`        | **ストリーミングチャット（SSE）**     |
| GET/POST/PATCH/DELETE | `/api/memories`          | 記憶の一覧 / 追加 / 編集 / 削除        |
| POST     | `/api/research`                       | リサーチ（要約 + 出典 + 画像）        |
| POST     | `/api/transcribe`                     | 音声ファイル → テキスト               |

### チャット SSE イベント

`data: {json}` 形式。`type` は `start` / `delta`(本文差分) / `tool`(検索などの進捗) /
`sources`(出典) / `done` / `memory`(抽出された記憶) / `error`。

## プロジェクト構成

```
backend/
  app/
    main.py            FastAPI 本体・ルーター登録
    config.py          設定（pydantic-settings）
    database.py models.py schemas.py  DB層
    prompts.py         人格・抽出・リサーチのプロンプト
    vectorstore.py     コサイン類似検索
    routers/           users/conversations/chat/memories/research/transcription
    services/          llm/embeddings/memory/search/web/research/transcription/tools
  tests/test_api.py    キー不要の基本APIテスト
frontend/
  src/
    App.tsx
    components/  GalaxyCanvas / Sidebar / ChatView / MessageList / Composer
                 / MemoryPanel / ResearchPanel
    hooks/       useChatStream(SSE) / useRecorder(録音)
    api.ts types.ts styles.css
```

## テスト

```bash
cd backend && source .venv/bin/activate && pytest     # APIキー不要で動作
cd frontend && npm run build                          # 型チェック + ビルド
```

## 本番運用に向けて（拡張ポイント）

- **PostgreSQL + pgvector**: `DATABASE_URL` を Postgres に変更。`models.Memory.embedding` を
  pgvector の `Vector` 型へ、`vectorstore.cosine_topk` を SQL の近傍検索へ置き換える。
- **認証 / マルチユーザー**: 現状は単一ユーザー（`/api/me` が既定ユーザーを返す）。
- **記憶抽出の非同期化**: 現在はチャット応答後に同期実行。ジョブキューへ移すと応答後の待ちが消える。

## ライセンス

個人利用向けのサンプル実装。
