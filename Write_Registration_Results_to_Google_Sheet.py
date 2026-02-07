
import os
from google_sheets_utils import get_google_sheets_service

def write_registration_results_to_google_sheet(results, items, year, month, day, hour, minute):
    """
    登録結果をGoogleスプレッドシートに書き込む関数

    Args:
        results (list): 登録結果のリスト（各要素は辞書形式）
        items (list): 商品情報のリスト（各要素は辞書形式）
        year (int): 現在の年
        month (int): 現在の月
        day (int): 現在の日
        hour (int): 現在の時
        minute (int): 現在の分
    """
    # Google Sheets APIのサービスを取得
    service = get_google_sheets_service()

    # スプレッドシートのID
    spreadsheet_id = os.getenv('SPREADSHEET_ID')

    # 書き込む範囲
    range_name = os.getenv('SHEET_NAME', 'RegistrationResults!A1')  # シート名を適宜変更

    # ヘッダー行
    values = [
        ['ItemCode', 'ShopID', 'ItemNumber', 'ItemName', 'ItemURL', 'RoomPostURL', 'Collection', 'Status', 'LastPostedDate', 'Collection_Status', 'Note', 'descriptions']
    ]

    # 現在の日時を文字列に
    timestamp = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

    # 登録結果を追加
    for result, item in zip(results, items):
        values.append([
            item.get('item_code', ''),  # ItemCode
            item.get('shop_id', ''),  # ShopID
            item.get('item_number', ''),  # ItemNumber
            item.get('name', ''),  # ItemName
            item.get('url', ''),  # ItemURL
            item.get('room_post_url', ''),  # RoomPostURL
            item.get('collection', ''),  # Collection
            result.get('status', ''),  # Status
            timestamp,  # LastPostedDate
            item.get('collection_status', ''),  # Collection_Status
            result.get('details', ''),  # Note
            item.get('description', '')  # descriptions
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