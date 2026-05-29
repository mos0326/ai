#!/usr/bin/env bash
# バックエンド開発サーバー起動
# 使い方: cd backend && ./run.sh
set -euo pipefail
cd "$(dirname "$0")"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
