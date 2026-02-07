"""
楽天Room投稿モジュール - 商品をROOMに投稿
"""
import asyncio
import pyperclip
from playwright.async_api import Page
from config import RAKUTEN_ROOM_BASE_URL


async def register_item_to_room(page: Page, item_code: str, description: str) -> bool:
    """
    商品をROOMに投稿
    
    Args:
        page: Playwrightのページオブジェクト
        item_code: 商品コード
        description: 紹介文
    
    Returns:
        bool: 投稿成功時True、失敗時False
    """
    try:
        # 商品ページを開く
        item_url = f"{RAKUTEN_ROOM_BASE_URL}/item/{item_code}"
        await page.goto(item_url)
        await page.wait_for_load_state('networkidle')
        
        print(f"商品ページを開きました: {item_url}")
        
        # 「ROOMに投稿」ボタンを探す
        post_button = await find_post_button(page)
        
        if not post_button:
            print(f"✗ 商品 {item_code}: 「ROOMに投稿」ボタンが見つかりません")
            return False
        
        # ボタンをクリック
        await post_button.click()
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
        print(f"「ROOMに投稿」ボタンをクリックしました")
        
        # 投稿モーダルまたは投稿フォームを待つ
        await asyncio.sleep(2)
        
        # 紹介文を入力するテキストエリアを探す
        description_textarea = await page.query_selector(
            "textarea[placeholder*='紹介文'], textarea.description, div[contenteditable='true']"
        )
        
        if description_textarea:
            # クリップボードに紹介文をコピー
            pyperclip.copy(description)
            
            # テキストエリアをクリック
            await description_textarea.click()
            await asyncio.sleep(0.5)
            
            # Ctrl+Aで全選択してから貼り付け
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Control+V')
            
            print(f"紹介文を入力しました")
            
            # 「完了」ボタンをクリック
            complete_button = await page.query_selector(
                "button:has-text('完了'), button:has-text('投稿する'), button.submit"
            )
            
            if complete_button:
                await complete_button.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                print(f"✓ 商品 {item_code}: ROOMへの投稿に成功しました")
                return True
            else:
                print(f"✗ 商品 {item_code}: 「完了」ボタンが見つかりません")
                return False
        else:
            print(f"✗ 商品 {item_code}: 紹介文入力フィールドが見つかりません")
            return False
    
    except Exception as e:
        print(f"✗ 商品 {item_code}: 投稿処理でエラーが発生しました: {e}")
        return False


async def find_post_button(page: Page):
    """
    「ROOMに投稿」ボタンを探す
    
    Args:
        page: Playwrightのページオブジェクト
    
    Returns:
        ボタン要素またはNone
    """
    # 複数のセレクタで検索
    selectors = [
        "button:has-text('ROOMに投稿')",
        "a:has-text('ROOMに投稿')",
        "button[data-test='post-to-room']",
        "button.room-post-button"
    ]
    
    for selector in selectors:
        try:
            button = await page.query_selector(selector)
            if button and await button.is_visible():
                return button
        except:
            continue
    
    return None


async def add_to_collection(page: Page, collection_name: str) -> bool:
    """
    投稿した商品をコレクションに追加
    
    Args:
        page: Playwrightのページオブジェクト
        collection_name: コレクション名
    
    Returns:
        bool: 追加成功時True、失敗時False
    """
    try:
        if not collection_name or collection_name.strip() == '':
            print("コレクション名が指定されていません")
            return False
        
        # コレクション追加ボタンを探す
        add_collection_button = await page.query_selector(
            "button:has-text('コレクションに追加'), button.add-to-collection"
        )
        
        if not add_collection_button:
            print("✗ コレクション追加ボタンが見つかりません")
            return False
        
        await add_collection_button.click()
        await asyncio.sleep(1)
        
        # コレクション選択ダイアログを待つ
        await page.wait_for_load_state('networkidle')
        
        # 指定されたコレクション名を探す
        collection_option = await page.query_selector(
            f"input[value='{collection_name}'], label:has-text('{collection_name}')"
        )
        
        if collection_option:
            await collection_option.click()
            await asyncio.sleep(1)
            
            # 「完了」または「保存」ボタンをクリック
            save_button = await page.query_selector(
                "button:has-text('完了'), button:has-text('保存')"
            )
            
            if save_button:
                await save_button.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                print(f"✓ コレクション '{collection_name}' に追加しました")
                return True
        
        print(f"✗ コレクション '{collection_name}' が見つかりません")
        return False
    
    except Exception as e:
        print(f"✗ コレクション追加処理でエラーが発生しました: {e}")
        return False
