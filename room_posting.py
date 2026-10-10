"""
楽天Room投稿モジュール - 商品をROOMに投稿
"""
import asyncio
from playwright.async_api import (
    ElementHandle,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
 
 
async def post_item_to_room(page: Page, description: str, shop_code: str) -> bool:
    """
    商品ページからROOMに投稿
 
    Args:
        page: Playwrightのページオブジェクト (商品ページの状態)
        description: 紹介文
        shop_code: ショップコード
 
    Returns:
        bool: 投稿成功時True、失敗時False
    """
    try:
        # ============================================================
        # 「ROOMに投稿」ボタンを探す
        # 通常ボタンが見つからない場合はシェアボタン経由で投稿する
        # ============================================================
 
        # ① 通常の「ROOMに投稿」ボタンを探す
        post_button = await find_post_button(page)
 
        if post_button:
            active_page = await click_and_get_target_page(page, post_button)
            print(f"[DEBUG] ROOMページへ遷移しました: {active_page.url}")
 
        else:
            # ② 通常ボタンが見つからない場合はシェアボタン経由で投稿
            print("[DEBUG] 通常の投稿ボタンが見つかりません。シェアボタンを試みます。")
 
            # シェアボタンを複数セレクタで探す
            share_selectors = [
                'button.snsShare__button',          # ① classで指定（最も確実）
                "button:has-text('シェア')",         # ② テキストで指定
                "a:has-text('シェア')",              # ③ aタグのテキストで指定
            ]
 
            share_button = None
            for selector in share_selectors:
                try:
                    share_button = await page.wait_for_selector(selector, timeout=5000)
                    if share_button:
                        print(f"[DEBUG] シェアボタンを発見しました（セレクタ: {selector}）")
                        break
                except Exception:
                    print(f"[DEBUG] セレクタが見つかりません、次を試します: {selector}")
                    continue
 
            if not share_button:
                print("✗ シェアボタンが見つかりません")
                return False
 
            await share_button.click()
            await asyncio.sleep(1)
 
            # シェアメニューからROOM投稿リンクを探す
            room_selectors = [
                'a.item__room',                             # ① classで指定（最も確実）
                'a[data-ratid="item_share_room"]',          # ② data属性で指定
                'a[href*="room.rakuten.co.jp/mix"]',        # ③ hrefで指定
                "a:has-text('ROOMに投稿する')",             # ④ テキストで指定
                "button:has-text('ROOMに投稿する')",        # ⑤ buttonタグで指定
            ]
 
            room_post_button = None
            for selector in room_selectors:
                try:
                    room_post_button = await page.wait_for_selector(selector, timeout=5000)
                    if room_post_button:
                        print(f"[DEBUG] ROOMに投稿ボタンを発見しました（セレクタ: {selector}）")
                        break
                except Exception:
                    print(f"[DEBUG] セレクタが見つかりません、次を試します: {selector}")
                    continue
 
            if not room_post_button:
                print("✗ 「ROOMに投稿する」ボタンが見つかりません")
                return False
 
            active_page = await click_and_get_target_page(page, room_post_button)
            print(f"[DEBUG] ROOMページへ遷移しました: {active_page.url}")
 
        await asyncio.sleep(2)
        print("「ROOMに投稿」ボタンをクリックしました")
 
        # ============================================================
        # 紹介文を入力するテキストエリアを探す
        # ボタンの実装により同一タブまたは新しいタブになるため、active_pageを操作する
        # ============================================================
 
        # item-name（商品名）が表示されるまで待つ
        # この要素が表示された = ページの読み込みが完了したと判断する
        try:
            await active_page.wait_for_selector('div.item-name', timeout=30000)
            print("[DEBUG] 商品名が表示されました。ページの読み込みが完了しました。")
        except Exception:
            print("[DEBUG] 商品名の表示確認がタイムアウトしました。処理を続行します。")
 
        description_selectors = [
            '#collect-content',                         # ① idで指定（最も確実）
            'textarea[name="content"]',                 # ② name属性で指定
            'textarea[ng-model="$parent.content"]',     # ③ ng-model属性で指定
            "textarea[placeholder*='紹介文']",          # ④ placeholder属性で指定
            'textarea.description',                     # ⑤ classで指定
            "div[contenteditable='true']",              # ⑥ contenteditable属性で指定
        ]
 
        description_textarea = None
        for selector in description_selectors:
            try:
                description_textarea = await active_page.wait_for_selector(selector, timeout=5000)
                if description_textarea:
                    print(f"[DEBUG] 紹介文欄を発見しました（セレクタ: {selector}）")
                    break
            except Exception:
                print(f"[DEBUG] セレクタが見つかりません、次を試します: {selector}")
                continue
 
        if not description_textarea:
            print("✗ 紹介文欄が見つかりませんでした。全セレクタが失敗しました。")
            return False
 
        # 紹介文を入力
        await description_textarea.fill(description)
        print("紹介文を入力しました")
 
        # ============================================================
        # 「完了」ボタンをクリック
        # ============================================================
        complete_selectors = [
            'button.collect-btn',                   # ① classで指定（最も具体的）
            'button[ng-click="collect()"]',         # ② ng-click属性で指定
            'button.button-red.collect-btn',        # ③ 複数classで指定
            "button:has-text('完了')",              # ④ ボタンのテキストで指定
            "button:has-text('投稿する')",          # ⑤ ボタンのテキストで指定
            'button.submit',                        # ⑥ classで指定
        ]
 
        complete_button = None
        for selector in complete_selectors:
            try:
                complete_button = await active_page.wait_for_selector(selector, timeout=5000)
                if complete_button:
                    print(f"[DEBUG] 完了ボタンを発見しました（セレクタ: {selector}）")
                    break
            except Exception:
                print(f"[DEBUG] セレクタが見つかりません、次を試します: {selector}")
                continue
 
        if not complete_button:
            print("✗ 完了ボタンが見つかりませんでした。全セレクタが失敗しました。")
            return False
 
        await complete_button.click()
        try:
            await active_page.wait_for_load_state('domcontentloaded', timeout=30000)
        except PlaywrightTimeoutError:
            pass
        await asyncio.sleep(2)
 
        # 投稿成功の確認（成功メッセージやページ遷移を確認）
        success_indicator = await find_visible_text(
            active_page,
            ('投稿が完了しました', '投稿しました', 'ROOMに投稿されました'),
        )
        try:
            compose_button_visible = await complete_button.is_visible()
        except Exception:
            compose_button_visible = False

        if success_indicator or (
            'room.rakuten.co.jp' in active_page.url and not compose_button_visible
        ):
            print("✓ ROOMへの投稿に成功しました")
            return True
        else:
            print("✗ 投稿成功の確認ができませんでした")
            return False
 
    except Exception as e:
        print(f"✗ 投稿処理でエラーが発生しました: {e}")
        return False
 
 
async def find_post_button(page: Page):
    """
    「ROOMに投稿」ボタンを探す
 
    Args:
        page: Playwrightのページオブジェクト
 
    Returns:
        ボタン要素またはNone
    """
    selectors = [
        "button[data-test='post-to-room']",
        "button[aria-label*='ROOMに投稿']",
        "button:has-text('ROOMに投稿')",
        "a:has-text('ROOMに投稿')",
        "button[data-test='room-post-button']",
        "button.room-post-button"
    ]
 
    for selector in selectors:
        try:
            button = await page.wait_for_selector(selector, timeout=3000)
            if button and await button.is_visible():
                return button
        except Exception:
            continue
 
    return None


async def click_and_get_target_page(page: Page, button: ElementHandle):
    """クリック後の同一タブ遷移と新規タブ表示を、最大120秒待って処理する。"""
    async def wait_for_new_page():
        async with page.context.expect_page(timeout=120000) as page_info:
            return await page_info.value

    new_page_task = asyncio.create_task(wait_for_new_page())
    same_page_task = asyncio.create_task(
        page.wait_for_url('**/room.rakuten.co.jp/**', timeout=120000)
    )

    try:
        await button.click()
        done, pending = await asyncio.wait(
            {new_page_task, same_page_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        target_page = new_page_task.result() if new_page_task in done else page
        await target_page.wait_for_load_state('domcontentloaded', timeout=120000)
        return target_page
    except (PlaywrightTimeoutError, asyncio.CancelledError):
        for task in (new_page_task, same_page_task):
            if not task.done():
                task.cancel()
        raise


async def find_visible_text(page: Page, texts: tuple[str, ...]) -> bool:
    """指定したいずれかの文言が表示されているか確認する。"""
    for text in texts:
        try:
            if await page.get_by_text(text, exact=False).first.is_visible(timeout=3000):
                return True
        except Exception:
            continue
    return False
 