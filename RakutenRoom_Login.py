from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def login_to_rakuten():
    user_id = os.getenv('RAKUTEN_USER_ID')
    pass_word = os.getenv('RAKUTEN_PASSWORD')
    # Edge の WebDriver を自動取得
    # 手動でダウンロードしたEdge WebDriverのパスを指定（例: ./drivers/msedgedriver.exe）
    # driver_path = os.getenv('DRIVER_PATH')  # 必要に応じてパスを調整
    # # WebDriverサービスを起動してEdgeドライバを起動
    # service = Service(executable_path=driver_path)
    # driver = webdriver.Edge(service=service)

    # driver = None
    driver_path = os.getenv('DRIVER_PATH')  # .env に設定したパス

    options = Options()
    options.add_argument("--headless")

    try:
        if driver_path and os.path.exists(driver_path):
            service = Service(driver_path)
            driver = webdriver.Edge(service=service)
        else:
            raise FileNotFoundError("指定された msedgedriver.exe が存在しません")

    except (SessionNotCreatedException, WebDriverException, FileNotFoundError) as e:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)

    # 楽天ルームのログインページを開く
    driver.get("https://room.rakuten.co.jp/all/items")

    # 2秒待機（ページ読み込みを待つ）
    time.sleep(2)

    try:
        # 「アカウント登録/ログイン」ボタンをクリック
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.signUp-loginBtn"))
        )
        login_btn.click()

        # ID入力欄の出現を待つ
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_id"))
        )

        # IDとパスワードを入力
        driver.find_element(By.ID, "user_id").send_keys(user_id)

        # 次へボタンをクリック
        next_button = driver.find_element(By.ID, "cta001")
        next_button.click()
        
        # パスワード入力欄の出現を待つ
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password_current"))
        )
    
        # パスワードを入力
        driver.find_element(By.ID, "password_current").send_keys(pass_word)

        # 次へボタンをクリック
        next_button = driver.find_element(By.ID, "cta011")
        next_button.click()

    except Exception as e:
        driver.quit()
        raise

    # 60秒待機（ログイン処理が完了するまで待つ）
    time.sleep(60)

    return driver