#!/bin/bash
# Claude Code on the web 用 SessionStart フック。
# バックエンド(venv+pip)とフロント(npm)の依存を導入し、テスト/型チェックが
# すぐ動く状態にする。冪等（複数回実行しても安全）。
set -euo pipefail

# Web(リモート)環境でのみ実行。ローカルでは何もしない。
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
ENV_FILE="${CLAUDE_ENV_FILE:-/dev/null}"

# --- Backend: venv + 依存 ---
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# セッション中、venv の python/pytest/uvicorn を使えるように
echo "export PATH=\"$ROOT/backend/.venv/bin:\$PATH\"" >> "$ENV_FILE"
# app パッケージを解決できるように
echo "export PYTHONPATH=\"$ROOT/backend:\${PYTHONPATH:-}\"" >> "$ENV_FILE"

# --- Frontend: node 依存 ---
cd "$ROOT/frontend"
npm install --no-audit --no-fund

echo "Personal AI: 依存の導入が完了しました。"
