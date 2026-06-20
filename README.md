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

#### 4. **google_sheets_utils.py**
- Google Sheets APIへの接続とサービスオブジェクトの取得
- サービスアカウント認証の管理

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
SERVICE_ACCOUNT_PATH=path/to/service_account.json
OPENAI_API_KEY=your_openai_api_key
PLAYWRIGHT_BROWSERS_PATH=path/to/ms-playwright
```

- `PLAYWRIGHT_BROWSERS_PATH` は必要に応じて指定します。
- 未指定の場合、実行ファイルでは `%LOCALAPPDATA%\ms-playwright` を自動検出します。

### 3. Google認証の設定
- Google Cloud Consoleでサービスアカウントを作成
- サービスアカウントのJSONキーをダウンロード
- ダウンロードしたJSONファイルのパスを `SERVICE_ACCOUNT_PATH` に設定

## 実行方法

### 通常実行
```bash
python main.py
```

> 現在、未投稿商品のうち最初の1件のみ処理します。

## 実行ファイルの作成

### 1. 実行ファイルを作成する手順
```bash
pyinstaller --onefile --name RakutenRoomAutoPost main.py
```

- `--onefile` を付けると `dist\RakutenRoomAutoPost.exe` が生成されます。
- `--onefile` を付けない場合は `dist\RakutenRoomAutoPost\` フォルダに実行ファイルと依存ファイルが出力されます。

### 2. 実行時に必要な外部ファイル
実行ファイルと同じ階層に `.env` を配置してください。`config.py` は実行ファイルのあるフォルダの `.env` を探して読み込みます。

- `dist\RakutenRoomAutoPost.exe`
- `dist\.env`
- サービスアカウントJSONファイル（`SERVICE_ACCOUNT_PATH` で指定）

### 3. Playwright のブラウザが必要
実行ファイルでも `playwright` のブラウザがインストールされている必要があります。生成前に以下を実行してください。

```bash
playwright install
```

- `playwright` はブラウザ操作のために必要です。
- Windows では通常、Playwright のブラウザは次のフォルダにインストールされます。
  - `%LOCALAPPDATA%\ms-playwright`
  - 例: `C:\Users\<ユーザー名>\AppData\Local\ms-playwright`
- `.env` の `PLAYWRIGHT_BROWSERS_PATH` を指定すれば、そのパスを優先します。

### 4. 配布先での配置
- 実行ファイルを配布する場合、`.env` は `RakutenRoomAutoPost.exe` と同じ階層に置きます。
- サービスアカウントJSONファイルも同じ階層に置くのが簡単です。
- Playwright のブラウザは、配布先環境でも `%LOCALAPPDATA%\ms-playwright` にインストールされている必要があります。

  配布先で Playwright ブラウザをインストールするには、同じように以下を実行します。

  ```bash
  playwright install
  ```

- `PLAYWRIGHT_BROWSERS_PATH` を環境変数や `.env` で明示的に指定している場合は、そのパスにブラウザファイルが必要です。

## ログ出力

ログファイルは `logs/` ディレクトリに以下のフォーマットで保存されます：
- ファイル名: `rakuten_room_YYYYMMDD_HHMMSS.log`

## トラブルシューティング

### ブラウザ接続エラー
- Playwrightが正しくインストールされているか確認
- `playwright install` で必要なブラウザをインストール

### Google Sheets認証エラー
- サービスアカウントJSONファイルが正しく配置されているか確認
- `SERVICE_ACCOUNT_PATH` が `.env` に設定されているか確認

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
