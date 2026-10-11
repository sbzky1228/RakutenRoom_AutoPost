"""
楽天Room投稿モジュール - 商品をROOMに投稿
"""
import asyncio
from enum import Enum
from playwright.async_api import (
    ElementHandle,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from logger import get_logger
from rakuten_login import complete_login_form, is_login_page
 
 
class PostResult(Enum):
    """ROOM投稿の結果"""
    POSTED = "新規投稿"                      # 新しくROOMに投稿（コレ！）した
    ALREADY_COLLECTED = "すでにコレ済み"     # 以前にROOMへ投稿済みの商品だった
    FAILED = "失敗"                          # 投稿できなかった

    @property
    def is_success(self) -> bool:
        """ROOMに登録されている状態になったか（新規投稿・すでにコレ済みのどちらも成功扱い）"""
        return self is not PostResult.FAILED


async def post_item_to_room(page: Page, description: str) -> PostResult:
    """
    商品ページからROOMに投稿
 
    Args:
        page: Playwrightのページオブジェクト (商品ページの状態)
        description: 紹介文
 
    Returns:
        PostResult: 新規投稿 / すでにコレ済み / 失敗
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
                get_logger().error("シェアボタンが見つかりません")
                return PostResult.FAILED
 
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
                get_logger().error("「ROOMに投稿する」ボタンが見つかりません")
                return PostResult.FAILED
 
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
            get_logger().error("紹介文欄が見つかりませんでした。全セレクタが失敗しました。")
            return PostResult.FAILED

        # すでにROOMに投稿（コレ！）済みの商品は、投稿画面の読み込み後に
        # 「すでにコレ！している商品です」ダイアログが出て「完了」が押せなくなる。
        # その場合はダイアログを閉じて、投稿済みとして扱う。
        if await is_already_collected(active_page):
            print("✓ すでにROOMに投稿済み（すでにコレ済み）の商品のため、新規投稿はせず投稿済みとして扱います")
            return PostResult.ALREADY_COLLECTED
 
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
            get_logger().error("完了ボタンが見つかりませんでした。全セレクタが失敗しました。")
            return PostResult.FAILED
 
        try:
            await complete_button.click(timeout=15000)
        except PlaywrightTimeoutError:
            # 「すでにコレ！している商品です」ダイアログが遅れて表示され、完了ボタンが押せなかった場合
            if await is_already_collected(active_page, timeout=1000):
                print("✓ すでにROOMに投稿済み（すでにコレ済み）の商品のため、新規投稿はせず投稿済みとして扱います")
                return PostResult.ALREADY_COLLECTED
            raise
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
            return PostResult.POSTED
        else:
            get_logger().error("投稿成功の確認ができませんでした")
            return PostResult.FAILED
 
    except Exception as e:
        get_logger().error(f"投稿処理でエラーが発生しました: {e}")
        return PostResult.FAILED
 
 
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


def is_room_or_login_page(url: str) -> bool:
    """ROOMのページ、またはROOM投稿前の再認証で表示される楽天のログイン画面かどうか"""
    return 'room.rakuten.co.jp' in url or is_login_page(url)


async def click_and_get_target_page(page: Page, button: ElementHandle):
    """
    クリック後の同一タブ遷移と新規タブ表示を、最大120秒待って処理する。
    ROOMへ遷移する前に再認証（楽天のログイン画面）を求められた場合は、認証を完了させてからROOMへ進む。
    遷移はURLの確定（commit）で判定する。ページの全リソース読み込み（load）は
    回線状況によって120秒を超えることがあり、待つ必要がないため。
    """
    async def wait_for_new_page():
        async with page.context.expect_page(timeout=120000) as page_info:
            new_page = await page_info.value
        await new_page.wait_for_url(is_room_or_login_page, wait_until='commit', timeout=120000)
        return new_page

    new_page_task = asyncio.create_task(wait_for_new_page())
    same_page_task = asyncio.create_task(
        page.wait_for_url(is_room_or_login_page, wait_until='commit', timeout=120000)
    )

    try:
        await button.click()
        done, _ = await asyncio.wait(
            {new_page_task, same_page_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        target_page = new_page_task.result() if new_page_task in done else page
        if target_page is page:
            same_page_task.result()  # タイムアウトしていれば例外を送出する

        if is_login_page(target_page.url):
            get_logger().info("ROOMへの投稿前に再認証を求められたため、ログインします")
            if not await complete_login_form(target_page):
                raise RuntimeError("ROOM投稿前の再認証に失敗しました")

        await target_page.wait_for_url('**/room.rakuten.co.jp/**', wait_until='commit', timeout=120000)
        await target_page.wait_for_load_state('domcontentloaded', timeout=120000)
        return target_page
    finally:
        # 待機タスクを片付け、未回収の例外（Task exception was never retrieved）を出さないようにする
        for task in (new_page_task, same_page_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(new_page_task, same_page_task, return_exceptions=True)


async def is_already_collected(page: Page, timeout: int = 5000) -> bool:
    """「すでにコレ！している商品です」ダイアログが出ているか確認し、出ていれば「OK」で閉じる。"""
    dialog_text = page.get_by_text("すでにコレ", exact=False).first
    try:
        await dialog_text.wait_for(state='visible', timeout=timeout)
    except PlaywrightTimeoutError:
        return False

    try:
        await page.get_by_text("OK", exact=True).first.click(timeout=5000)
    except Exception:
        pass
    return True


async def find_visible_text(page: Page, texts: tuple[str, ...]) -> bool:
    """指定したいずれかの文言が表示されているか確認する。"""
    for text in texts:
        try:
            if await page.get_by_text(text, exact=False).first.is_visible(timeout=3000):
                return True
        except Exception:
            continue
    return False
 