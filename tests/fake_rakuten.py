"""
テスト用の偽の楽天サイト

Playwrightの通信差し替え（route）で、楽天のログイン画面・my Rakuten・商品ページ・ROOM投稿画面を再現する。
実際の楽天には一切アクセスしない（想定外のURLはすべて遮断する）ため、
テストでROOMに投稿されたり、楽天アカウントがロックされたりすることはない。

再現している実際の画面の流れ（2026年10月に調査）:
- ログイン: ユーザーID →「次へ」→ パスキー要求（navigator.credentials.get）
  → キャンセルされると「パスキーを確認できませんでした」「パスワードを使用する」→ パスワード →「次へ」
- ROOM投稿時の再認証（/session/upgrade）:「〇〇として続けますか？」→「次へ」（div要素）→ 以降は同上
- my Rakuten: ログイン済みでも読み込み直後は「ログイン」を仮表示し、少し後に「ログアウト」に切り替わる
- ROOM投稿画面: 投稿済みの商品は読み込み後に「すでにコレ！している商品です」ダイアログが出る
"""
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from urllib.parse import parse_qs, quote, urlparse

from playwright.async_api import async_playwright

from browser_manager import CANCEL_PASSKEY_SCRIPT

CORRECT_PASSWORD = "correct-password"
MY_RAKUTEN_URL = "https://my.rakuten.co.jp/"
ITEM_URL = "https://item.rakuten.co.jp/test-shop/test-item/"
ITEM_CODE = "test-shop:test-item"


@dataclass
class FakeRakutenState:
    """偽の楽天サイトの状態（テストから設定・確認する）"""
    logged_in: bool = False             # my Rakutenでログイン済みとして表示するか
    require_reauth: bool = False        # ROOM投稿時に再認証（/session/upgrade）を求めるか
    collected: set = field(default_factory=set)   # すでにコレ済みの商品コード
    login_page_hits: int = 0            # ログイン画面が表示された回数
    posts: list = field(default_factory=list)     # ROOMに投稿された内容


LOGIN_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>楽天会員 ログイン</title></head>
<body><div id="app"></div><script>
const params = new URLSearchParams(location.search);
const next = params.get('next') || '__MY_URL__';
const app = document.getElementById('app');
window.__pwSubmits = 0;
function show(html) { app.innerHTML = html; }

function idScreen() {
  show('<p>楽天会員 ログイン</p><input id="user_id" name="username"><div id="cta001" role="button">次へ</div>');
  document.getElementById('cta001').onclick = () => {
    if (document.getElementById('user_id').value) passkeyScreen();
  };
}
function continueScreen() {
  show('<p>「パスキー」に進みます</p><p>user@example.comとして続けますか？</p><div id="prim_81" role="button">次へ</div>');
  document.getElementById('prim_81').onclick = passkeyScreen;
}
async function passkeyScreen() {
  show('<p>パスキーで認証しています</p>');
  try {
    await navigator.credentials.get({publicKey: {
      challenge: new Uint8Array(32), timeout: 600000,
      allowCredentials: [{type: 'public-key', id: new Uint8Array(16)}]}});
    show('<p>パスキーで認証しました</p>');
  } catch (e) {
    window.__passkeyError = e.name;
    show('<p>パスキーを確認できませんでした</p>' +
         '<div id="prim_570" role="button">もう一度パスキーを試す</div>' +
         '<div id="seco_571" role="button">パスワードを使用する</div>');
    document.getElementById('seco_571').onclick = passwordScreen;
  }
}
function passwordScreen() {
  show('<p>ようこそ user@example.com</p><input id="password_current" type="password">' +
       '<div id="cta011" role="button">次へ</div><p id="err"></p>');
  document.getElementById('cta011').onclick = () => {
    window.__pwSubmits++;
    if (document.getElementById('password_current').value === '__PASSWORD__') {
      location.href = '/complete?next=' + encodeURIComponent(next);
    } else {
      document.getElementById('err').textContent = 'ユーザIDまたはパスワードが正しくありません';
    }
  };
}
if (location.pathname.startsWith('/session/upgrade')) continueScreen(); else idScreen();
</script></body></html>"""

MY_RAKUTEN_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>my Rakuten</title></head>
<body><header><a id="header-login" href="__LOGIN_URL__">ログイン</a></header><main id="main"></main><script>
// 実際のmy Rakutenと同様、確定するまで「ログイン」を仮表示する
setTimeout(() => {
  if (__LOGGED_IN__) {
    document.querySelector('header').innerHTML = '<a href="#">ログアウト</a>';
    document.getElementById('main').innerHTML = '<p>こんにちは テスト さん</p>';
  } else {
    document.getElementById('main').innerHTML =
      '<p>my Rakutenへようこそ</p><p>ご利用にはログインが必要です</p><a href="__LOGIN_URL__">ログイン</a>';
  }
}, 1000);
</script></body></html>"""

ITEM_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>テスト商品</title></head>
<body><h1>テスト商品</h1>
<a aria-label="ROOMに投稿" href="https://room.rakuten.co.jp/mix?itemcode=__ITEM_CODE__" target="_self">ROOMに投稿</a>
</body></html>"""

COLLECT_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>ROOM</title>
<style>#dialog{position:fixed;inset:0;background:rgba(0,0,0,.5)}</style></head>
<body><p>コレ！して投稿する</p><div class="item-name">テスト商品</div>
<textarea id="collect-content" name="content"></textarea>
<button class="button button-red collect-btn">完了</button><p id="result"></p>
<script>
document.querySelector('.collect-btn').onclick = async () => {
  await fetch('/api/collect', {method: 'POST', body: document.getElementById('collect-content').value});
  document.querySelector('.collect-btn').style.display = 'none';
  document.getElementById('result').textContent = '投稿しました';
};
if (__ALREADY__) {
  // 実際のROOMと同様、読み込み後少し遅れてダイアログが出て、完了ボタンを覆う
  setTimeout(() => {
    const d = document.createElement('div');
    d.id = 'dialog';
    d.innerHTML = '<div><p>すでにコレ！している商品です</p><button id="ok">OK</button></div>';
    document.body.appendChild(d);
    document.getElementById('ok').onclick = () => d.remove();
  }, 500);
}
</script></body></html>"""

REDIRECT_PAGE = """<!doctype html><html><head><meta charset="utf-8"></head>
<body><script>location.replace(__TARGET__);</script></body></html>"""


def _html(route, body: str):
    return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)


def _redirect(route, target: str):
    return _html(route, REDIRECT_PAGE.replace("__TARGET__", json.dumps(target)))


def _login_url(next_url: str, path: str = "/sso/authorize") -> str:
    return f"https://login.account.rakuten.com{path}?next={quote(next_url, safe='')}"


async def _handle(route, state: FakeRakutenState):
    url = urlparse(route.request.url)
    query = parse_qs(url.query)
    host, path = url.hostname, url.path

    if host == "login.account.rakuten.com":
        if path == "/complete":
            # パスワード認証に成功した（再認証の場合はROOMへ戻る）
            next_url = query.get("next", [MY_RAKUTEN_URL])[0]
            state.logged_in = True
            if "room.rakuten.co.jp" in next_url:
                state.require_reauth = False
            return await _redirect(route, next_url)
        state.login_page_hits += 1
        return await _html(route, LOGIN_PAGE.replace("__MY_URL__", MY_RAKUTEN_URL)
                           .replace("__PASSWORD__", CORRECT_PASSWORD))

    if host == "my.rakuten.co.jp":
        return await _html(route, MY_RAKUTEN_PAGE
                           .replace("__LOGGED_IN__", "true" if state.logged_in else "false")
                           .replace("__LOGIN_URL__", _login_url(MY_RAKUTEN_URL)))

    if host == "item.rakuten.co.jp":
        return await _html(route, ITEM_PAGE.replace("__ITEM_CODE__", quote(ITEM_CODE, safe="")))

    if host == "room.rakuten.co.jp":
        item_code = query.get("itemcode", [""])[0]
        if path == "/mix":
            collect_url = f"https://room.rakuten.co.jp/mix/collect?itemcode={quote(item_code, safe='')}"
            if state.require_reauth:
                return await _redirect(route, _login_url(collect_url, path="/session/upgrade"))
            return await _redirect(route, collect_url)
        if path == "/mix/collect":
            return await _html(route, COLLECT_PAGE.replace(
                "__ALREADY__", "true" if item_code in state.collected else "false"))
        if path == "/api/collect":
            state.posts.append(route.request.post_data)
            return await route.fulfill(status=200, body="ok")

    # 想定外のURL（実際のインターネット）への通信はすべて遮断する
    return await route.abort()


@asynccontextmanager
async def fake_rakuten_browser(state: FakeRakutenState):
    """
    偽の楽天サイトにつながったブラウザのページを返す。
    本番の BrowserManager と同様に、パスキーをキャンセルするスクリプトを注入する。
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_init_script(CANCEL_PASSKEY_SCRIPT)
        async def handler(route):
            await _handle(route, state)

        await context.route("**/*", handler)
        page = await context.new_page()
        page.set_default_timeout(30000)
        try:
            yield page
        finally:
            await browser.close()
