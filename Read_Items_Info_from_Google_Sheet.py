
import os
from google_sheets_utils import get_google_sheets_service

def read_items_info_from_google_sheet():
    """
    Googleスプレッドシートから商品情報を取得する関数

    Returns:
        list: 商品情報のリスト（各要素は辞書形式）
    """
    # Google Sheets APIのサービスを取得
    service = get_google_sheets_service()

    # スプレッドシートのID
    spreadsheet_id = os.getenv('SPREADSHEET_ID')

    # 読み取る範囲（例: 'Items!A2:Z'）ヘッダー行を除く
    range_name = os.getenv('SHEET_NAME') + '!A2:Z'  # シート名を適宜変更

    # スプレッドシートからデータを取得
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    items = []
    if values:
        # ヘッダー行をスキップ
        data_rows = values[1:]
        for row in data_rows:
            if len(row) >= 12:  # ヘッダーの列数
                item = {
                    'item_code': row[0] if len(row) > 0 else '',
                    'shop_id': row[1] if len(row) > 1 else '',
                    'item_number': row[2] if len(row) > 2 else '',
                    'name': row[3] if len(row) > 3 else '',
                    'url': row[4] if len(row) > 4 else '',
                    'room_post_url': row[5] if len(row) > 5 else '',
                    'collection': row[6] if len(row) > 6 else '',
                    'status': row[7] if len(row) > 7 else '',
                    'last_posted_date': row[8] if len(row) > 8 else '',
                    'collection_status': row[9] if len(row) > 9 else '',
                    'note': row[10] if len(row) > 10 else '',
                    'description': row[11] if len(row) > 11 else ''
                }
                items.append(item)

    return items