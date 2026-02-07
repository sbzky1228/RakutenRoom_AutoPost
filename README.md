# 楽天Room自動投稿プログラム - Playwright版

## プログラム構成

このプログラムは、楽天市場のお気に入り商品情報を取得し、楽天ROOMに自動で投稿するためのツールです。

### 主要モジュール

#### 1. **config.py**
- 環境変数の読み込みと設定管理
- 楽天、Google Sheets、OpenAI のAPIキー
- アプリケーション全体の定数設定

#### 2. **browser_manager.py**
- Playwrightを使用したブラウザ管理
- ページ操作（遷移、待機など）
- ブラウザのライフサイクル管理

#### 3. **rakuten_login.py**
- 楽天へのログイン処理
- ログイン認証情報の入力

#### 4. **fetch_favorites.py**
- 楽天市場のお気に入り商品情報取得
- URLからの商品情報抽出
- 楽天APIを使用した詳細情報取得

#### 5. **google_sheets_manager.py**
- Google Sheets APIの操作
- 商品情報の読み書き
- ステータス更新処理

#### 6. **chatgpt_manager.py**
- ChatGPT APIを使用した紹介文生成
- OpenAIとの通信管理

#### 7. **room_posting.py**
- ROOMへの商品投稿処理
- コレクションへの追加処理

#### 8. **logger.py**
- ログ出力管理
- ログファイルの記録

#### 9. **main.py**
- メイン処理（各モジュールの統合）
- 処理フロー全体の制御

### 処理フロー

```
1. ブラウザ起動
2. 楽天へのログイン
3. お気に入り商品情報の取得
4. Google Sheetsへの情報追加
5. 未投稿商品の取得
6. ChatGPTで紹介文生成
7. 各商品をROOMに投稿
   ├─ 投稿処理
   ├─ Google Sheets更新
   └─ コレクション追加
8. ブラウザ終了
```

## セットアップ手順

### 1. 環境構築
```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
.\venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt

# Playwrightの初期化
playwright install
```

### 2. .env ファイルの作成
```
RAKUTEN_USER_ID=your_user_id
RAKUTEN_PASSWORD=your_password
SPREADSHEET_ID=your_spreadsheet_id
SHEET_NAME=Sheet1
RAKUTEN_APP_ID=your_app_id
OPENAI_API_KEY=your_openai_api_key
DRIVER_PATH=
```

### 3. Google認証の設定
- Google Cloud ConsoleでOAuth 2.0認証情報を作成
- `client_secret_*.json` ファイルをプロジェクトディレクトリに配置

## 実行方法

### 通常実行
```bash
python main.py
```

### テスト実行
```bash
python test.py
```

## ログ出力

ログファイルは `logs/` ディレクトリに以下のフォーマットで保存されます：
- ファイル名: `rakuten_room_YYYYMMDD_HHMMSS.log`

## トラブルシューティング

### ブラウザ接続エラー
- Playwrightが正しくインストールされているか確認
- `playwright install` で必要なブラウザをインストール

### Google Sheets認証エラー
- OAuth 2.0認証情報が正しく配置されているか確認
- 古い `token.pickle` を削除して再認証

### ChatGPT エラー
- OpenAI APIキーが正しいか確認
- APIアカウントのクォータ確認

## 必要な環境

- Python 3.8以上
- Google Sheetsアカウント
- OpenAIアカウント
- 楽天市場アカウント

## ライセンス

このプログラムは個人使用を想定しています。

## 更新履歴

### v2.0 (2024-02-08)
- Seleniumから Playwrightへ移行
- 非同期処理の導入
- エラーハンドリングの強化
- ロギング機能の改善
