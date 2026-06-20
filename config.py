"""
設定ファイル - 環境変数や定数を管理
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _resolve_env_path() -> Path | None:
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys._MEIPASS) / '.env')
        candidates.append(Path(sys.executable).resolve().parent / '.env')
    candidates.append(Path.cwd() / '.env')
    candidates.append(Path(__file__).resolve().parent / '.env')
    for path in candidates:
        if path.exists():
            return path.resolve()
    return None


def _resolve_path_from_env(value: str, base_dir: Path) -> str:
    if not value:
        return ''
    path = Path(value)
    if path.is_absolute():
        return str(path)

    candidate = base_dir / path
    if candidate.exists():
        return str(candidate.resolve())

    candidate = Path.cwd() / path
    if candidate.exists():
        return str(candidate.resolve())

    candidate = Path(__file__).resolve().parent / path
    return str(candidate.resolve())


# .envファイルを読み込む
ENV_PATH = _resolve_env_path()
if ENV_PATH:
    load_dotenv(str(ENV_PATH))
    ENV_DIR = ENV_PATH.parent
else:
    load_dotenv('.env')
    ENV_DIR = Path.cwd()

# 楽天ログイン情報
RAKUTEN_USER_ID = os.getenv('RAKUTEN_USER_ID', '')
RAKUTEN_PASSWORD = os.getenv('RAKUTEN_PASSWORD', '')

# Google Sheets情報
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')
SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')
SERVICE_ACCOUNT_PATH = _resolve_path_from_env(os.getenv('SERVICE_ACCOUNT_PATH', ''), ENV_DIR)  # サービスアカウントのパス

# API情報
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Playwrightの設定
# - PLAYWRIGHT_BROWSERS_PATH は .env または環境変数から読み取ります
# - 実行ファイル起動時に未指定の場合は、Windowsの既定パス (%LOCALAPPDATA%\ms-playwright) を自動検出します
PLAYWRIGHT_BROWSERS_PATH = _resolve_path_from_env(os.getenv('PLAYWRIGHT_BROWSERS_PATH', ''), ENV_DIR)
CHROMIUM_EXECUTABLE_PATH = _resolve_path_from_env(os.getenv('CHROMIUM_EXECUTABLE_PATH', ''), ENV_DIR)

if not PLAYWRIGHT_BROWSERS_PATH and getattr(sys, 'frozen', False):
    default_playwright = Path(os.path.expanduser('~')) / 'AppData' / 'Local' / 'ms-playwright'
    if default_playwright.exists():
        PLAYWRIGHT_BROWSERS_PATH = str(default_playwright)

if PLAYWRIGHT_BROWSERS_PATH:
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = PLAYWRIGHT_BROWSERS_PATH

HEADLESS_MODE = False    # ヘッドレスモード
BROWSER_TIMEOUT = 60000  # タイムアウト（ミリ秒）
PAGE_LOAD_TIMEOUT = 10000  # ページロード待機時間
NAVIGATION_TIMEOUT = 60000  # ナビゲーション待機時間

# Google Sheets APIスコープ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Rakuten Room / Ichiba URLs
RAKUTEN_ROOM_BASE_URL = "https://room.rakuten.co.jp"
RAKUTEN_ICHIBA_BASE_URL = "https://www.rakuten.co.jp"
