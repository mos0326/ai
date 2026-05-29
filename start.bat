@echo off
rem Personal AI ワンクリック起動（Windows）。エクスプローラで start.bat をダブルクリック。
cd /d "%~dp0"

rem --- Python コマンド検出（python か py） ---
set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if not defined PYEXE ( where py >nul 2>&1 && set "PYEXE=py" )
if not defined PYEXE (
  echo [エラー] Python が見つかりません。Python 3 をインストールしてください。
  pause
  exit /b 1
)

rem --- Node/npm 検出 ---
where npm >nul 2>&1
if errorlevel 1 (
  echo [エラー] npm(Node.js) が見つかりません。Node.js をインストールしてください。
  pause
  exit /b 1
)

echo Personal AI を起動します...

rem --- バックエンド: venv + 依存 + .env ---
cd backend
if not exist .venv (
  echo Python 仮想環境を作成中...
  %PYEXE% -m venv .venv
)
call .venv\Scripts\activate.bat
echo バックエンド依存を確認/導入中...（初回は数分かかることがあります）
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if not exist .env copy ..\.env.example .env >nul
start "Personal AI backend" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

rem --- フロント: 依存 ---
cd ..\frontend
if not exist node_modules (
  echo フロント依存を導入中...（初回のみ数分かかります）
  call npm install --no-audit --no-fund
)
start "Personal AI frontend" cmd /k "npx vite --port 5173"

echo 起動中... 数秒後にブラウザを開きます。
timeout /t 6 >nul
start "" http://localhost:5173

echo.
echo ====================================================
echo  ブラウザで  http://localhost:5173  を開きます。
echo  開いた2つの黒いウィンドウは閉じないでください。
echo  （サーバーが動いています。停止はそのウィンドウを閉じる）
echo ====================================================
pause
