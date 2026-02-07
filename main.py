"""
メインプログラム - 楽天Room自動投稿
"""
import asyncio
import datetime
from browser_manager import create_browser_manager
from rakuten_login import login_to_rakuten
from fetch_favorites import get_favorite_items_info
from google_sheets_manager import GoogleSheetsManager
from chatgpt_manager import generate_descriptions_for_items
from room_posting import register_item_to_room, add_to_collection
from logger import Logger


async def main():
    """メイン処理"""
    logger = Logger()
    browser_manager = None
    
    try:
        logger.info("=" * 80)
        logger.info("楽天Room自動投稿プログラムを開始します")
        logger.info("=" * 80)
        
        # 現在の日時を取得
        now = datetime.datetime.now()
        posted_date = now.strftime('%Y-%m-%d')
        
        # ブラウザを起動
        logger.info("ブラウザを起動しています...")
        browser_manager = await create_browser_manager()
        page = await browser_manager.get_page()
        
        # 楽天にログイン
        logger.info("楽天にログインしています...")
        if not await login_to_rakuten(page):
            logger.error("楽天へのログインに失敗しました")
            return
        
        # お気に入り商品情報を取得
        logger.info("お気に入り商品情報を取得しています...")
        favorite_items = await get_favorite_items_info(page, max_items=200)
        
        if not favorite_items:
            logger.warning("お気に入り商品が見つかりません")
            return
        
        logger.info(f"{len(favorite_items)}件のお気に入り商品を取得しました")
        
        # Google Sheetsに商品情報を追加
        logger.info("Google Sheetsに商品情報を追加しています...")
        sheets_manager = GoogleSheetsManager()
        sheets_manager.append_items(favorite_items)
        
        # 未投稿の商品を取得
        logger.info("未投稿の商品を取得しています...")
        unposted_items = sheets_manager.get_unposted_items()
        
        if not unposted_items:
            logger.info("投稿対象の商品がありません")
            return
        
        logger.info(f"{len(unposted_items)}件の投稿対象商品があります")
        
        # ChatGPTで紹介文を生成
        logger.info("ChatGPTで紹介文を生成しています...")
        descriptions = generate_descriptions_for_items(unposted_items)
        
        # 各商品をROOMに投稿
        logger.info("商品をROOMに投稿しています...")
        for item in unposted_items:
            item_code = item.get('ItemCode', '')
            item_name = item.get('ItemName', '')
            collection = item.get('Collection', '')
            
            if not item_code:
                logger.warning(f"商品コードが不明なため、スキップしています: {item_name}")
                continue
            
            # 紹介文を取得
            description = descriptions.get(item_code, '')
            if not description:
                logger.warning(f"紹介文の生成に失敗したため、スキップしています: {item_name}")
                continue
            
            # ROOMに投稿
            logger.info(f"商品を投稿しています: {item_name}")
            success = await register_item_to_room(page, item_code, description)
            
            if success:
                # Google Sheetsの投稿ステータスを更新
                sheets_manager.update_post_status(item_code, posted_date)
                
                # コレクションに追加
                if collection:
                    logger.info(f"コレクションに追加しています: {collection}")
                    collection_success = await add_to_collection(page, collection)
                    
                    if collection_success:
                        sheets_manager.update_collection_status(item_code, posted_date)
            else:
                logger.warning(f"商品の投稿に失敗しました: {item_name}")
                continue
        
        logger.info("=" * 80)
        logger.info("楽天Room自動投稿プログラムが完了しました")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # ブラウザを閉じる
        if browser_manager:
            logger.info("ブラウザを閉じています...")
            await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())