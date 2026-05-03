"""
設定ファイル - 環境変数や定数を管理
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv('.env')

# 楽天ログイン情報
RAKUTEN_USER_ID = os.getenv('RAKUTEN_USER_ID', '')
RAKUTEN_PASSWORD = os.getenv('RAKUTEN_PASSWORD', '')

# Google Sheets情報
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')
SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', '')  # サービスアカウントのパス

# API情報
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Playwrightの設定
HEADLESS_MODE = False    # ヘッドレスモード
BROWSER_TIMEOUT = 60000  # タイムアウト（ミリ秒）
PAGE_LOAD_TIMEOUT = 10000  # ページロード待機時間
NAVIGATION_TIMEOUT = 60000  # ナビゲーション待機時間

# Google Sheets APIスコープ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Rakuten Room / Ichiba URLs
RAKUTEN_ROOM_BASE_URL = "https://room.rakuten.co.jp"
RAKUTEN_ICHIBA_BASE_URL = "https://www.rakuten.co.jp"
