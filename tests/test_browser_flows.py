"""
ブラウザを使った結合テスト

偽の楽天サイト（tests/fake_rakuten.py）に対して、本番のログイン処理・ROOM投稿処理をそのまま動かす。
実際の楽天にはアクセスしない。
"""
import asyncio
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

import browser_manager
import rakuten_login
from rakuten_login import complete_login_form, login_to_rakuten
from room_posting import PostResult, is_already_collected, post_item_to_room
from tests.fake_rakuten import (
    COLLECT_PAGE, ITEM_CODE, ITEM_URL, MY_RAKUTEN_URL, FakeRakutenState, fake_rakuten_browser,
)


def read_log(test_logger) -> str:
    return Path(test_logger.log_file).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# パスキーのキャンセル
# ---------------------------------------------------------------------------

def credentials_get_js(options: str) -> str:
    """navigator.credentials.get の結果（成功 or 例外名: メッセージ）を返すJS"""
    return f"""async () => {{
      try {{ await navigator.credentials.get({options}); return 'resolved'; }}
      catch (e) {{ return e.name + ': ' + e.message; }}
    }}"""


def test_passkey_request_is_cancelled_but_password_lookup_is_not():
    async def scenario():
        async with fake_rakuten_browser(FakeRakutenState()) as page:
            await page.goto(MY_RAKUTEN_URL)  # navigator.credentials は https のページでのみ使える
            passkey = await page.evaluate(credentials_get_js("{publicKey: {challenge: new Uint8Array(32)}}"))
            password = await page.evaluate(credentials_get_js("{password: true}"))
            return passkey, password

    passkey, password = asyncio.run(scenario())
    # パスキー要求は「ユーザーがキャンセルした」のと同じ NotAllowedError で即失敗する（QRダイアログは出ない）
    assert passkey == "NotAllowedError: Passkey was cancelled by automation."
    # 保存済みパスワードの照会（publicKeyなし）はブラウザ本来の処理に任せる
    assert "cancelled by automation" not in password


def test_browser_manager_injects_cancel_script_and_uses_app_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(browser_manager, "HEADLESS_MODE", True)
    monkeypatch.setattr(browser_manager, "APP_DIR", tmp_path)

    async def scenario():
        manager = await browser_manager.create_browser_manager()
        try:
            page = await manager.get_page()
            await manager.context.route("**/*", lambda route: route.fulfill(
                status=200, content_type="text/html", body="<html><body>ok</body></html>"))
            await page.goto("https://example.test/")
            return await page.evaluate(credentials_get_js("{publicKey: {challenge: new Uint8Array(32)}}"))
        finally:
            await manager.close()

    assert asyncio.run(scenario()).startswith("NotAllowedError")
    # ログインセッションは APP_DIR/user_data に保存される
    assert (tmp_path / "user_data").is_dir()


# ---------------------------------------------------------------------------
# ログイン
# ---------------------------------------------------------------------------

def test_login_skipped_when_session_is_valid(credentials):
    state = FakeRakutenState(logged_in=True)

    async def scenario():
        async with fake_rakuten_browser(state) as page:
            return await login_to_rakuten(page)

    # my Rakuten は読み込み直後に「ログイン」を仮表示するが、ログイン済みと正しく判定する
    assert asyncio.run(scenario()) is True
    assert state.login_page_hits == 0


def test_first_login_cancels_passkey_and_uses_password(credentials, log_to_tmp):
    state = FakeRakutenState(logged_in=False)

    async def scenario():
        async with fake_rakuten_browser(state) as page:
            return await login_to_rakuten(page), page.url

    ok, url = asyncio.run(scenario())
    assert ok is True
    assert url == MY_RAKUTEN_URL
    log = read_log(log_to_tmp)
    assert "ユーザーIDを入力しました" in log
    assert "パスキー認証をキャンセルし、パスワードでのログインに切り替えます" in log
    assert "パスワードを入力しました" in log
    assert "楽天市場へのログインに成功しました" in log


def test_wrong_password_is_submitted_only_once(monkeypatch, log_to_tmp):
    monkeypatch.setattr(rakuten_login, "RAKUTEN_USER_ID", "user@example.com")
    monkeypatch.setattr(rakuten_login, "RAKUTEN_PASSWORD", "wrong-password")

    async def scenario():
        async with fake_rakuten_browser(FakeRakutenState()) as page:
            await page.goto("https://login.account.rakuten.com/sso/authorize")
            ok = await complete_login_form(page, timeout=60000)
            return ok, await page.evaluate("window.__pwSubmits")

    ok, submits = asyncio.run(scenario())
    assert ok is False
    # アカウントロックを防ぐため、誤ったパスワードを再送信しない
    assert submits == 1
    assert "[ERROR] パスワードを送信しましたがログインできませんでした" in read_log(log_to_tmp)


def test_login_form_without_credentials_does_nothing(monkeypatch, log_to_tmp):
    monkeypatch.setattr(rakuten_login, "RAKUTEN_USER_ID", "")
    monkeypatch.setattr(rakuten_login, "RAKUTEN_PASSWORD", "")

    async def scenario():
        async with fake_rakuten_browser(FakeRakutenState()) as page:
            await page.goto("https://login.account.rakuten.com/sso/authorize")
            return await complete_login_form(page), await page.locator("#user_id").input_value()

    ok, typed = asyncio.run(scenario())
    assert ok is False
    assert typed == ""
    assert "[ERROR] 楽天のログイン情報が設定されていません。" in read_log(log_to_tmp)


# ---------------------------------------------------------------------------
# ROOM投稿
# ---------------------------------------------------------------------------

def post_scenario(state: FakeRakutenState, description="テストの紹介文です。"):
    async def scenario():
        async with fake_rakuten_browser(state) as page:
            await page.goto(ITEM_URL, wait_until="domcontentloaded")
            return await post_item_to_room(page, description)
    return asyncio.run(scenario())


def test_post_new_item(credentials):
    state = FakeRakutenState(logged_in=True)
    assert post_scenario(state, "新しい紹介文") is PostResult.POSTED
    assert state.posts == ["新しい紹介文"]


def test_post_already_collected_item(credentials):
    state = FakeRakutenState(logged_in=True, collected={ITEM_CODE})
    assert post_scenario(state) is PostResult.ALREADY_COLLECTED
    # すでにコレ済みの商品は投稿しない
    assert state.posts == []


def test_post_with_reauthentication(credentials, log_to_tmp):
    # ROOM投稿ボタンを押すと /session/upgrade の再認証が入るケース
    state = FakeRakutenState(logged_in=True, require_reauth=True)
    assert post_scenario(state, "再認証後の紹介文") is PostResult.POSTED
    assert state.posts == ["再認証後の紹介文"]
    log = read_log(log_to_tmp)
    assert "ROOMへの投稿前に再認証を求められたため、ログインします" in log
    assert "再認証の確認画面で「次へ」をクリックしました" in log
    assert "パスキー認証をキャンセルし、パスワードでのログインに切り替えます" in log


@pytest.mark.parametrize("already", [True, False])
def test_is_already_collected(already):
    async def scenario():
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(COLLECT_PAGE.replace("__ALREADY__", "true" if already else "false"))
            result = await is_already_collected(page, timeout=3000)
            dialog_left = await page.locator("#dialog").count()
            await browser.close()
            return result, dialog_left

    result, dialog_left = asyncio.run(scenario())
    assert result is already
    # ダイアログは「OK」で閉じる
    assert dialog_left == 0
