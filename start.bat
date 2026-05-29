@echo off
rem Personal AI ワンコマンド起動（Windows）。ダブルクリック、または start.bat で実行。
rem 初回は依存を自動インストールし、バックエンドとフロントを別ウィンドウで起動します。
setlocal
cd /d "%~dp0"

echo Personal AI を起動します...

cd backend
if not exist .venv (
  echo Python 仮想環境を作成中...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo バックエンド依存を確認/導入中...（初回は数分かかることがあります）
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if not exist .env copy ..\.env.example .env >nul

rem バックエンドを別ウィンドウで起動
start "Personal AI backend" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

cd ..\frontend
if not exist node_modules (
  echo フロント依存を導入中...（初回のみ数分かかります）
  call npm install --no-audit --no-fund
)
rem フロントを別ウィンドウで起動
start "Personal AI frontend" cmd /k "npx vite --port 5173"

echo 起動中... 数秒後にブラウザを開きます。
timeout /t 5 >nul
start "" http://localhost:5173

echo.
echo 開いたウィンドウは閉じないでください（サーバーが動いています）。
echo 停止するには、起動した2つのウィンドウを閉じてください。
endlocal
