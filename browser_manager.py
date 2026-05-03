"""
ブラウザ管理モジュール - Playwrightを使用したブラウザ操作
"""
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from config import HEADLESS_MODE, BROWSER_TIMEOUT, NAVIGATION_TIMEOUT

class BrowserManager:
    """Playwrightを使用したブラウザ実装を管理するクラス"""
    
    def __init__(self):
        # 初期化: Playwright、Browser、Pageオブジェクトを保持する変数
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def launch(self):
        """
        ブラウザを起動
        
        1. Playwrightを初期化
        2. Chromiumブラウザを読動
        3. 新しいページを作成
        4. タイムアウトを設定
        """
        self.playwright = await async_playwright().start()
        
        # Chromiumブラウザを起動（headlessモードは設定値で決定）
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS_MODE)
        
        # 新しいページを作成
        self.page = await self.browser.new_page()
        
        # タイムアウトを設定。謟隊承起時間内を矢接後、エラーを発生
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        
        # ナビゲーション待機時間を設定
        self.page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        
        return self.page
    
    async def close(self):
        """ブラウザを閉じる"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def get_page(self) -> Page:
        """ページオブジェクトを取得"""
        return self.page


async def create_browser_manager() -> BrowserManager:
    """BrowserManagerインスタンスを生成"""
    manager = BrowserManager()
    await manager.launch()
    return manager
