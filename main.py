"""
メインプログラム - 楽天Room自動投稿 (ROOM登録のみ)
"""
import asyncio
import datetime
from browser_manager import create_browser_manager
from rakuten_login import login_to_rakuten
from google_sheets_manager import GoogleSheetsManager
from google_sheets_utils import connect_to_sheets_and_get_existing_codes
from chatgpt_manager import generate_description
from room_posting import PostResult, post_item_to_room
from logger import get_logger


async def main():
    """メイン処理"""
    logger = get_logger()
    browser_manager = None

    try:
        logger.info("=" * 80)
        logger.info("楽天Room自動投稿プログラムを開始します")
        logger.info("=" * 80)

        # 現在の日時を取得
        now = datetime.datetime.now()
        posted_date = now.strftime('%Y-%m-%d')

        # Google Sheetsマネージャーを初期化
        logger.info("スプレッドシートへの接続を確認しています...")
        service, existing_item_codes = connect_to_sheets_and_get_existing_codes()

        if service is None:
            logger.error("スプレッドシートへの接続に失敗しました。処理を終了します。")
            return

        logger.info(f"接続成功（既存商品数: {len(existing_item_codes)}件）")

        sheets_manager = GoogleSheetsManager(service)

        # PostStatusが「未」の商品を取得
        logger.info("Googleスプレッドシートから未投稿の商品を取得しています...")
        unposted_items = sheets_manager.get_unposted_items()

        if not unposted_items:
            logger.info("投稿対象の商品がありません")
            return

        logger.info(f"{len(unposted_items)}件の投稿対象商品があります")

        # 最初の1件だけ処理
        item = unposted_items[0]
        logger.info(f"取得した投稿対象商品(1件): {item}")

        # ブラウザを起動
        logger.info("ブラウザを起動しています...")
        browser_manager = await create_browser_manager()
        page = await browser_manager.get_page()

        # 楽天にログイン
        logger.info("楽天にログインしています...")
        if not await login_to_rakuten(page):
            logger.error("楽天へのログインに失敗しました")
            return

        # 1件だけ処理
        item_url = item.get('ItemURL', '')
        item_name = item.get('ItemName', '')

        if not item_url or not item_name:
            logger.warning(f"必要な情報が不足しているため、処理を中止します: {item_name}")
            return

        logger.info(f"商品を処理しています: {item_name}")

        # 商品ページを開く
        # 商品ページは広告等の読み込みが重く'load'まで60秒を超えることがあるため、
        # DOMの読み込み完了で先に進み、'load'は待てる範囲で待つ
        await page.goto(item_url, wait_until='domcontentloaded')
        try:
            await page.wait_for_load_state('load', timeout=30000)
        except Exception:
            logger.info("商品ページの全リソース読み込みを待たずに処理を続行します")

        # ChatGPTで紹介文を生成
        logger.info(f"ChatGPTで紹介文を生成しています: {item_name}")
        description = generate_description(item_name)
        if not description:
            logger.warning(f"紹介文の生成に失敗したため、処理を中止します: {item_name}")
            sheets_manager.update_post_status_by_url(item_url, '不可', posted_date)
            return

        # ROOMに投稿
        logger.info(f"ROOMに投稿しています: {item_name}")
        result = await post_item_to_room(page, description)
        logger.info(f"投稿結果: {result.value}")

        if result is PostResult.POSTED:
            logger.info(f"【新規投稿】ROOMに新しく投稿しました: {item_name}")
        elif result is PostResult.ALREADY_COLLECTED:
            logger.info(f"【すでにコレ済み】ROOMに投稿済みの商品のため、新規投稿はしていません: {item_name}")

        if result.is_success:
            # 新規投稿・すでにコレ済みの場合はスプレッドシートのPostStatusを「済」、PostedDateを投稿日で更新する
            sheets_manager.update_post_status_by_url(item_url, '済', posted_date)
        else:
            logger.warning(f"【失敗】投稿に失敗しました: {item_name}")
            # 投稿失敗の場合はスプレッドシートのPostStatusを「不可」、PostedDateを投稿日で更新する
            sheets_manager.update_post_status_by_url(item_url, '不可', posted_date)

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