
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def update_collections_in_rakuten_room(driver, collections):
    """
    楽天ルームでコレクションを更新する関数

    Args:
        driver (WebDriver): SeleniumのWebDriverインスタンス
        collections (list): コレクション情報のリスト（各要素は辞書形式）
    """
    results = []
    for collection in collections:
        try:
            # コレクション管理ページに移動（仮定）
            driver.get("https://room.rakuten.co.jp/collections")  # 実際のURLを確認
            time.sleep(2)

            # コレクションを選択または作成（セレクタはサイト構造による）
            # 例: コレクション名で検索
            collection_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, collection.get('name', '')))
            )
            collection_link.click()

            # 商品を追加（仮定）
            add_item_button = driver.find_element(By.ID, "add_item_button")
            add_item_button.click()

            # 商品を選択（items から）
            for item_name in collection.get('items', '').split(','):
                item_checkbox = driver.find_element(By.XPATH, f"//input[@value='{item_name.strip()}']")
                item_checkbox.click()

            # 保存ボタンをクリック
            save_button = driver.find_element(By.ID, "save_button")
            save_button.click()

            time.sleep(5)

            results.append({
                'name': collection.get('name', ''),
                'status': '成功',
                'details': '更新完了'
            })

        except Exception as e:
            results.append({
                'name': collection.get('name', ''),
                'status': '失敗',
                'details': str(e)
            })

    return results