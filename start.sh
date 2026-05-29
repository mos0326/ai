#!/usr/bin/env bash
# Personal AI ワンコマンド起動スクリプト。
#   ./start.sh
# 初回は依存を自動インストールし、バックエンド(8000)とフロント(5173)を同時に起動する。
# 停止は Ctrl+C。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Personal AI を起動します…"

# --- バックエンド: venv + 依存 + .env ---
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  echo "  • Python 仮想環境を作成中…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
echo "  • バックエンド依存を確認/導入中…"
pip install -q --upgrade pip
pip install -q -r requirements.txt
if [ ! -f .env ]; then
  echo "  • backend/.env を作成しました（APIキーは後で記入できます）。"
  cp "$ROOT/.env.example" .env
fi

# --- フロント: 依存 ---
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  echo "  • フロント依存を導入中（初回のみ少し時間がかかります）…"
  npm install --no-audit --no-fund
fi

# --- 両方を起動し、Ctrl+C でまとめて停止 ---
PIDS=()
cleanup() {
  echo
  echo "■ 停止します…"
  for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

( cd "$ROOT/backend" && exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ) &
PIDS+=("$!")

( cd "$ROOT/frontend" && exec ./node_modules/.bin/vite --port 5173 ) &
PIDS+=("$!")

echo
echo "✅ 起動しました。ブラウザで  http://localhost:5173  を開いてください。"
echo "   バックエンドAPI: http://localhost:8000/docs"
echo "   停止: Ctrl+C"
echo
wait
