"""
楽天ログインモジュール - Playwrightを使用した楽天市場へのログイン処理
"""
import asyncio
from playwright.async_api import Page
from config import RAKUTEN_USER_ID, RAKUTEN_PASSWORD, RAKUTEN_ICHIBA_BASE_URL, NAVIGATION_TIMEOUT


async def login_to_rakuten(page: Page) -> bool:
    """
    楽天市場にログイン

    楽天市場のログインページから認証し、楽天市場の状態で商品ページへ遷移できるようにします。

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

    try:
        # 楽天市場トップページに移動
        await page.goto(RAKUTEN_ICHIBA_BASE_URL, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(1)

        # ログイン画面へ遷移するボタンがあればクリック
        login_button = await wait_for_selector_safe("[aria-label='ログイン'], a:has-text('ログイン'), button:has-text('ログイン')")
        if login_button:
            await login_button.click()
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(1)

        # ユーザーID入力フィールドを取得
        user_id_input = await wait_for_selector_safe(
            "input[id='user_id'], input[name='loginId'], input[id='loginId'], input[placeholder='ユーザーID']"
        )
        if not user_id_input:
            print("ユーザーID入力フィールドが見つかりませんでした")
            return False

        await user_id_input.fill(RAKUTEN_USER_ID)
        await asyncio.sleep(0.5)

        # ID入力後に次へボタンがある場合はクリック
        next_button = await wait_for_selector_safe("button[type='submit'], button:has-text('次へ'), div[id='cta001'], input[type='submit']")
        if next_button:
            await next_button.click()
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(1)

        # パスワード入力フィールドを取得
        password_input = await wait_for_selector_safe(
            "input[id='password_current'], input[type='password'], input[id='loginUserInner_password']"
        )
        if not password_input:
            print("パスワード入力フィールドが見つかりませんでした")
            return False

        await password_input.fill(RAKUTEN_PASSWORD)
        await asyncio.sleep(0.5)

        # ログイン実行ボタンをクリックまたはEnter
        submit_button = await wait_for_selector_safe(
            "button[type='submit'], button:has-text('ログイン'), div[id='cta011'], input[type='submit']"
        )
        if submit_button:
            await submit_button.click()
        else:
            await password_input.press('Enter')

        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)

        current_url = page.url
        if 'my.rakuten' in current_url or 'rakuten.co.jp' in current_url:
            print("楽天市場へのログインに成功しました")
            return True

        print("楽天市場へのログインに失敗しました。現在のURL:", current_url)
        return False

    except Exception as e:
        print(f"ログイン処理でエラーが発生しました: {e}")
        return False
