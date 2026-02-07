
import os
from google_sheets_utils import get_google_sheets_service

def read_collections_from_google_sheet():
    """
    Googleスプレッドシートからコレクション情報を取得する関数

    Returns:
        list: コレクション情報のリスト（各要素は辞書形式）
    """
    # Google Sheets APIのサービスを取得
    service = get_google_sheets_service()

    # スプレッドシートのID
    spreadsheet_id = os.getenv('SPREADSHEET_ID')

    # 読み取る範囲（例: 'Collections!A2:Z'）
    range_name = os.getenv('SHEET_NAME')  # シート名を適宜変更

    # スプレッドシートからデータを取得
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    collections = []
    if values:
        # ヘッダー行をスキップ
        data_rows = values[1:]
        for row in data_rows:
            if len(row) >= 3:  # 最低限の列数
                collection = {
                    'name': row[0] if len(row) > 0 else '',
                    'items': row[1] if len(row) > 1 else '',
                    'status': row[2] if len(row) > 2 else ''
                }
                collections.append(collection)

    return collections