
import os
from google_sheets_utils import get_google_sheets_service

def write_collection_results_to_google_sheet(results, collections, year, month, day, hour, minute):
    """
    コレクション登録結果をGoogleスプレッドシートに書き込む関数

    Args:
        results (list): コレクション登録結果のリスト
        collections (list): コレクション情報のリスト
        year (int): 現在の年
        month (int): 現在の月
        day (int): 現在の日
        hour (int): 現在の時
        minute (int): 現在の分
    """
    # Google Sheets APIのサービスを取得
    service = get_google_sheets_service()

    # スプレッドシートのID（環境変数から取得、またはハードコード）
    spreadsheet_id = os.getenv('SPREADSHEET_ID')

    # 書き込む範囲（例: 'Sheet1!A1'）
    range_name = os.getenv('SHEET_NAME', 'Collections!A1')  # シート名を適宜変更

    # ヘッダー行
    values = [
        ['ItemCode', 'ShopID', 'ItemNumber', 'ItemName', 'ItemURL', 'RoomPostURL', 'Collection', 'Status', 'LastPostedDate', 'Collection_Status', 'Note', 'descriptions']
    ]

    # 現在の日時を文字列に
    timestamp = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

    # コレクションの結果を追加
    for result, collection in zip(results, collections):
        values.append([
            '',  # ItemCode
            '',  # ShopID
            '',  # ItemNumber
            collection.get('name', ''),  # ItemName
            '',  # ItemURL
            '',  # RoomPostURL
            '',  # Collection
            result.get('status', ''),  # Status
            timestamp,  # LastPostedDate
            '',  # Collection_Status
            result.get('details', ''),  # Note
            ''  # descriptions
        ])

    # 書き込みリクエストのボディ
    body = {
        'values': values
    }

    # スプレッドシートに書き込む
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"{result.get('updatedCells')} セルが更新されました。")