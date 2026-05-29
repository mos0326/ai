#!/usr/bin/env bash
# Personal AI ワンコマンド起動スクリプト（Mac / Linux / WSL / Git Bash）。
#   ./start.sh
# 初回は依存を自動インストールし、バックエンド(8000)とフロント(5173)を同時に起動する。
# 停止は Ctrl+C。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Personal AI を起動します…"

# --- 必要コマンドの確認 ---
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "✋ Python が見つかりません。Python 3 をインストールしてください。"
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "✋ npm(Node.js) が見つかりません。Node.js をインストールしてください。"
  exit 1
fi

# --- バックエンド: venv + 依存 + .env ---
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  echo "  • Python 仮想環境を作成中…"
  "$PY" -m venv .venv
fi
# venv の実行ディレクトリ（Mac/Linux=bin, Windows/Git Bash=Scripts）
if [ -d .venv/bin ]; then VBIN="$ROOT/backend/.venv/bin"; else VBIN="$ROOT/backend/.venv/Scripts"; fi
# shellcheck disable=SC1090
. "$VBIN/activate"
echo "  • バックエンド依存を確認/導入中…（初回は数分かかることがあります）"
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if [ ! -f .env ]; then
  echo "  • backend/.env を作成しました（APIキーは後で記入できます）。"
  cp "$ROOT/.env.example" .env
fi

# --- フロント: 依存 ---
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  echo "  • フロント依存を導入中…（初回のみ数分かかります）"
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

( cd "$ROOT/backend" && exec "$VBIN/uvicorn" app.main:app --reload --host 0.0.0.0 --port 8000 ) &
PIDS+=("$!")

( cd "$ROOT/frontend" && exec ./node_modules/.bin/vite --port 5173 ) &
PIDS+=("$!")

# --- 少し待ってからブラウザを自動で開く（best-effort） ---
URL="http://localhost:5173"
(
  sleep 4
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
  elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$URL"
  fi
) >/dev/null 2>&1 &

echo
echo "✅ 起動しました。ブラウザで  $URL  を開いてください（自動で開かない場合は手動で）。"
echo "   バックエンドAPI: http://localhost:8000/docs"
echo "   ※ このターミナルは動いたままが正常です。停止は Ctrl+C。"
echo
wait
