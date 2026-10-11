"""
Google Sheetsマネージャー - Google Sheetsへのデータ読み書き

【認証方式】
サービスアカウント方式を使用しています。
トークンの期限切れや更新処理は不要です。
"""
from typing import List, Dict
from googleapiclient.errors import HttpError
from config import SPREADSHEET_ID, SHEET_NAME


class GoogleSheetsManager:
    """Google Sheets APIを操作するクラス"""
    
    def __init__(self, service):
        self.service = service
        self.spreadsheet_id = SPREADSHEET_ID
        self.sheet_name = SHEET_NAME
    
    def _get_col_index_from_header(self, header):
        """ヘッダー行から列インデックスを取得"""
        col_index = {}
        required_columns = ['ItemURL', 'ShopCode', 'ItemID', 'ItemCode', 'ItemName', 'CollectionName', 'CollectionGenre', 'PostStatus', 'PostedDate', 'CollectionStatus', 'CollectedDate']
        
        for col_name in required_columns:
            try:
                col_index[col_name] = header.index(col_name)
            except ValueError:
                print(f"✗ 必須列 '{col_name}' が見つかりません")
                return None
        
        return col_index
    
    def _rows_to_items(self, values, col_index):
        """スプレッドシートの行をアイテムの辞書リストに変換"""
        items = []
        
        # ヘッダー行をスキップして処理
        for row in values[1:] if len(values) > 1 else []:
            if len(row) > col_index['PostStatus']:
                post_status = row[col_index['PostStatus']] if row[col_index['PostStatus']] else ''
                if post_status == '未':  # 未投稿の場合のみ
                    items.append({
                        'ItemURL': row[col_index['ItemURL']] if len(row) > col_index['ItemURL'] else '',
                        'ShopCode': row[col_index['ShopCode']] if len(row) > col_index['ShopCode'] else '',
                        'ItemID': row[col_index['ItemID']] if len(row) > col_index['ItemID'] else '',
                        'ItemCode': row[col_index['ItemCode']] if len(row) > col_index['ItemCode'] else '',
                        'ItemName': row[col_index['ItemName']] if len(row) > col_index['ItemName'] else '',
                        'CollectionName': row[col_index['CollectionName']] if len(row) > col_index['CollectionName'] else '',
                        'CollectionGenre': row[col_index['CollectionGenre']] if len(row) > col_index['CollectionGenre'] else '',
                        'PostStatus': row[col_index['PostStatus']] if len(row) > col_index['PostStatus'] else '',
                        'PostedDate': row[col_index['PostedDate']] if len(row) > col_index['PostedDate'] else '',
                        'CollectionStatus': row[col_index['CollectionStatus']] if len(row) > col_index['CollectionStatus'] else '',
                        'CollectedDate': row[col_index['CollectedDate']] if len(row) > col_index['CollectedDate'] else ''
                    })
        
        return items
    
    def get_unposted_items(self) -> List[Dict]:
        """未投稿の商品情報を取得（ヘッダーから列位置を動的に決定）"""
        try:
            range_name = f"{self.sheet_name}!A:K"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("✓ スプレッドシートにデータがありません")
                return []
            
            # ヘッダー行から列インデックスを取得
            col_index = self._get_col_index_from_header(values[0])
            if col_index is None:
                return []
            
            items = self._rows_to_items(values, col_index)
            print(f"✓ 未投稿の商品数: {len(items)}")
            return items
        
        except HttpError as e:
            print(f"✗ スプレッドシートからのデータ取得に失敗しました: {e}")
            return []
        except Exception as e:
            print(f"✗ スプレッドシートからのデータ取得に失敗しました: {e}")
            return []
    
    def update_post_status_by_url(self, item_url: str, status: str, posted_date: str):
        """ItemURLで該当行の投稿ステータスと投稿日を更新（ヘッダーから列位置を動的に決定）

        PostStatus列に投稿状態を、PostedDate列に投稿日を設定します。
        """
        try:
            range_name = f"{self.sheet_name}!A:K"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("✗ スプレッドシートにデータがありません")
                return False
            
            # ヘッダー行から列インデックスを取得
            header = values[0]
            try:
                item_url_col = header.index('ItemURL')
                post_status_col = header.index('PostStatus')
                posted_date_col = header.index('PostedDate')
            except ValueError:
                print("✗ 必須列 'ItemURL', 'PostStatus' または 'PostedDate' が見つかりません")
                return False
            
            matched_rows = [
                (i, row) for i, row in enumerate(values[1:], start=2)
                if len(row) > item_url_col and row[item_url_col] == item_url
            ]
            # 同じURLの行が重複している場合は、投稿対象として取得された「未」の行を優先して更新する
            unposted_rows = [
                (i, row) for i, row in matched_rows
                if len(row) > post_status_col and row[post_status_col] == '未'
            ]
            target_rows = unposted_rows or matched_rows
            if not target_rows:
                print(f"✗ ItemURL {item_url} が見つかりません")
                return False

            # PostStatusとPostedDateの列を動的に決定して更新
            row_number = target_rows[0][0]
            update_range = f"{self.sheet_name}!{chr(65 + post_status_col)}{row_number}:{chr(65 + posted_date_col)}{row_number}"
            update_body = {'values': [[status, posted_date]]}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=update_body
            ).execute()

            print(f"✓ 商品 {item_url} の投稿ステータスを '{status}' に更新しました")
            return True

        except HttpError as e:
            print(f"✗ ステータス更新に失敗しました: {e}")
            return False
        except Exception as e:
            print(f"✗ ステータス更新に失敗しました: {e}")
            return False
