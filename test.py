"""
テストスクリプト - 各モジュールの動作確認用
"""
import asyncio
from browser_manager import create_browser_manager


async def test_browser_connection():
    """ブラウザ接続テスト"""
    print("ブラウザ接続テストを実行しています...")
    
    try:
        manager = await create_browser_manager()
        page = await manager.get_page()
        
        # Google検索ページを開いてテスト
        await page.goto("https://www.google.com")
        await page.wait_for_load_state('networkidle')
        
        print("✓ ブラウザ接続テスト成功")
        
        await manager.close()
        return True
    
    except Exception as e:
        print(f"✗ ブラウザ接続テスト失敗: {e}")
        return False


def test_config():
    """設定ファイルテスト"""
    print("設定ファイルテストを実行しています...")
    
    try:
        from config import RAKUTEN_USER_ID, SPREADSHEET_ID, OPENAI_API_KEY
        
        if not RAKUTEN_USER_ID:
            print("✗ RAKUTEN_USER_IDが設定されていません")
            return False
        
        if not SPREADSHEET_ID:
            print("✗ SPREADSHEET_IDが設定されていません")
            return False
        
        if not OPENAI_API_KEY:
            print("✗ OPENAI_API_KEYが設定されていません")
            return False
        
        print("✓ 設定ファイルテスト成功")
        return True
    
    except Exception as e:
        print(f"✗ 設定ファイルテスト失敗: {e}")
        return False


def test_google_sheets():
    """Google Sheetsテスト"""
    print("Google Sheetsテストを実行しています...")
    
    try:
        from google_sheets_manager import GoogleSheetsManager
        
        manager = GoogleSheetsManager()
        print("✓ Google Sheetsマネージャーの初期化成功")
        
        return True
    
    except Exception as e:
        print(f"✗ Google Sheetsテスト失敗: {e}")
        return False


async def run_all_tests():
    """すべてのテストを実行"""
    print("=" * 80)
    print("テストスイートを開始します")
    print("=" * 80)
    
    results = []
    
    results.append(("設定ファイルテスト", test_config()))
    results.append(("Google Sheetsテスト", test_google_sheets()))
    results.append(("ブラウザ接続テスト", await test_browser_connection()))
    
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ すべてのテストが成功しました")
    else:
        print("\n✗ いくつかのテストが失敗しました")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
