"""
楽天ログインモジュール - Playwrightを使用した楽天市場へのログイン処理
セッション保持（永続化）対応版
"""
import asyncio
from playwright.async_api import Page
from config import (
    RAKUTEN_USER_ID,
    RAKUTEN_PASSWORD,
    RAKUTEN_ICHIBA_BASE_URL,
    NAVIGATION_TIMEOUT,
)


async def login_to_rakuten(page: Page) -> bool:
    """
    楽天市場にログイン

    楽天市場のログインページから認証し、楽天市場の状態で商品ページへ遷移できるようにします。
    ※永続セッションにより既にログイン済みの場合は入力をスキップします。

    Args:
        page: Playwrightのページオブジェクト

    Returns:
        bool: ログイン成功時True、失敗時False
    """
    async def wait_for_selector_safe(selector: str, timeout: int = 5000):
        try:
            return await page.wait_for_selector(selector, timeout=timeout)
        except Exception:
            return None

    async def is_logged_in(timeout: int = 5000) -> bool:
        # ログアウトリンクはa要素で、画面上の文字は内部のspanに入っている。
        logout_link = page.locator(
            "a[href*='/logout'], a[aria-label='ログアウト']"
        ).filter(has_text="ログアウト")
        logout_text = page.get_by_text("ログアウト", exact=True)
        deadline = asyncio.get_running_loop().time() + (timeout / 1000)

        while asyncio.get_running_loop().time() < deadline:
            if await logout_link.count() > 0 or await logout_text.count() > 0:
                print("ログアウト表示を検出しました。ログイン済みです。")
                return True
            await asyncio.sleep(0.1)

        print("ログイン済み表示を検出できませんでした。")
        print(f"判定時のホスト: {page.url.split('/', 3)[2] if '://' in page.url else page.url}")
        print(f"ページタイトル: {await page.title()}")
        return False

    try:
        # 楽天市場トップページに移動
        await page.goto(RAKUTEN_ICHIBA_BASE_URL, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(5)

        # 【セッション判定】既にログイン済みか確認（マイページリンクやユーザー情報要素の確認）
        # ログイン済みの場合はID入力へ進まず成功とする
        if await is_logged_in():
            print("保存されたセッションにより、既にログイン済みです。")
            return True

        # ログイン済みでない場合は、ログインボタンがあるときだけログインを開始する
        login_button = await wait_for_selector_safe("[aria-label='ログイン'], a:has-text('ログイン'), button:has-text('ログイン')")
        if not login_button:
            print("ログイン済み表示もログインボタンも見つかりませんでした。")
            return False

        if not RAKUTEN_USER_ID or not RAKUTEN_PASSWORD:
            print("楽天のログイン情報が設定されていません。")
            return False

        await login_button.click()
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(1)

        # ユーザーID入力フィールドを取得
        user_id_input = await wait_for_selector_safe(
            "input[id='user_id'], input[name='loginId'], input[id='loginId'], input[placeholder='ユーザーID']"
        )
        if not user_id_input:
            if await is_logged_in(timeout=5000):
                print("ログイン済みを確認しました。")
                return True
            print("ユーザーID入力フィールドが見つかりませんでした")
            return False

        await user_id_input.fill(RAKUTEN_USER_ID)
        await asyncio.sleep(0.5)

        # 1. ユーザーID入力後に「次へ」をクリックする
        user_id_next_button = await wait_for_selector_safe(
            "button:has-text('次へ'), input[value='次へ'], div[id='cta001']",
            timeout=5000,
        )
        if not user_id_next_button:
            print("ユーザーID画面の「次へ」ボタンが見つかりませんでした")
            return False
        await user_id_next_button.click()
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(5)

        # パスワード入力画面でパスワードを入力する
        password_selector = (
            "input[id='password_current'], input[type='password'], "
            "input[id='loginUserInner_password']"
        )
        password_input = await wait_for_selector_safe(password_selector, timeout=8000)
        if not password_input:
            print("パスワード入力フィールドが見つかりませんでした")
            return False

        await password_input.fill(RAKUTEN_PASSWORD)
        await asyncio.sleep(0.5)

        # パスワード入力後に「次へ」をクリックする
        password_next_button = await wait_for_selector_safe(
            "button:has-text('次へ'), input[value='次へ'], div[id='cta011']",
            timeout=5000,
        )
        if not password_next_button:
            print("パスワード画面の「次へ」ボタンが見つかりませんでした")
            return False
        await password_next_button.click()

        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)

        current_url = page.url
        if 'my.rakuten' in current_url or 'rakuten.co.jp' in current_url:
            print("楽天市場へのログインに成功しました")
            return True

        print("楽天市場へのログインに失敗しました。現在のURL:", current_url)
        return False

    except Exception as e:
        print(f"ログイン処理でエラーが発生しました: {e}")
        return False