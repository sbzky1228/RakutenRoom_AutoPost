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
    
    def append_items(self, items: List[Dict]):
        """商品情報を追加"""
        try:
            values = []
            for item in items:
                values.append([
                    item.get('ItemURL', ''),
                    item.get('ShopCode', ''),
                    item.get('ItemID', ''),
                    item.get('ItemCode', ''),
                    item.get('ItemName', ''),
                    item.get('CollectionName', ''),
                    item.get('CollectionGenre', ''),
                    item.get('PostStatus', ''),
                    item.get('PostedDate', ''),
                    item.get('CollectionStatus', ''),
                    item.get('CollectedDate', '')
                ])
            
            range_name = f"{self.sheet_name}!A2"
            body = {'values': values}
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✓ {len(items)}件の商品情報をスプレッドシートに追加しました")
        
        except HttpError as e:
            print(f"✗ スプレッドシートへの追加に失敗しました: {e}")
        except Exception as e:
            print(f"✗ スプレッドシートへの追加に失敗しました: {e}")
    
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
                post_status_col = header.index('PostStatus')
                posted_date_col = header.index('PostedDate')
            except ValueError:
                print("✗ 必須列 'PostStatus' または 'PostedDate' が見つかりません")
                return False
            
            for i, row in enumerate(values[1:], start=2):
                if len(row) > 0 and row[0] == item_url:
                    # PostStatusとPostedDateの列を動的に決定して更新
                    update_range = f"{self.sheet_name}!{chr(65 + post_status_col)}{i}:{chr(65 + posted_date_col)}{i}"
                    update_body = {'values': [[status, posted_date]]}
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=update_body
                    ).execute()
                    
                    print(f"✓ 商品 {item_url} の投稿ステータスを '{status}' に更新しました")
                    return True
            
            print(f"✗ ItemURL {item_url} が見つかりません")
            return False
        
        except HttpError as e:
            print(f"✗ ステータス更新に失敗しました: {e}")
            return False
        except Exception as e:
            print(f"✗ ステータス更新に失敗しました: {e}")
            return False
    
    def update_collection_status(self, item_code: str, collected_date: str):
        """コレクション登録ステータスを更新"""
        try:
            range_name = f"{self.sheet_name}!A:K"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            for i, row in enumerate(values[1:], start=2):
                if len(row) > 3 and row[3] == item_code:
                    # I列（CollectionStatus）とJ列（CollectedDate）を更新
                    update_range = f"{self.sheet_name}!I{i}:J{i}"
                    update_body = {'values': [['済', collected_date]]}
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=update_body
                    ).execute()
                    
                    print(f"✓ 商品 {item_code} のコレクション登録ステータスを更新しました")
                    return True
            
            print(f"✗ 商品コード {item_code} が見つかりません")
            return False
        
        except HttpError as e:
            print(f"✗ コレクション登録ステータス更新に失敗しました: {e}")
            return False
        except Exception as e:
            print(f"✗ コレクション登録ステータス更新に失敗しました: {e}")
            return False
