"""ブラウザを使わない単体テスト（設定・スプレッドシート・ChatGPT・ログ）"""
from pathlib import Path
from types import SimpleNamespace

import chatgpt_manager
import config
import logger as logger_module
from google_sheets_manager import GoogleSheetsManager
from rakuten_login import is_login_page
from room_posting import PostResult, is_room_or_login_page

PROJECT_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def test_app_dir_is_project_dir_when_not_frozen():
    # python main.py で実行したときは、user_data・logs をプロジェクト直下に作る
    assert config.APP_DIR == PROJECT_DIR


def test_resolve_path_from_env(tmp_path):
    (tmp_path / "service_account.json").write_text("{}")
    assert config._resolve_path_from_env("", tmp_path) == ""
    # 相対パスは .env のあるフォルダを基準に解決する
    assert config._resolve_path_from_env("service_account.json", tmp_path) == str(tmp_path / "service_account.json")
    absolute = str(tmp_path / "other.json")
    assert config._resolve_path_from_env(absolute, PROJECT_DIR) == absolute


# ---------------------------------------------------------------------------
# URL判定・投稿結果
# ---------------------------------------------------------------------------

def test_is_login_page():
    assert is_login_page("https://login.account.rakuten.com/sso/authorize?client_id=x")
    assert is_login_page("https://login.account.rakuten.com/session/upgrade?token=x#/sign_in/webauthn")
    assert not is_login_page("https://my.rakuten.co.jp/")


def test_is_room_or_login_page():
    assert is_room_or_login_page("https://room.rakuten.co.jp/mix/collect?itemcode=1")
    assert is_room_or_login_page("https://login.account.rakuten.com/session/upgrade")
    assert not is_room_or_login_page("https://item.rakuten.co.jp/shop/item/")


def test_post_result_is_success():
    # 新規投稿・すでにコレ済みはシートを「済」、失敗は「不可」にする
    assert PostResult.POSTED.is_success
    assert PostResult.ALREADY_COLLECTED.is_success
    assert not PostResult.FAILED.is_success


# ---------------------------------------------------------------------------
# スプレッドシート（Google Sheets API は偽物に置き換える）
# ---------------------------------------------------------------------------

HEADER = ['ItemURL', 'ShopCode', 'ItemID', 'ItemCode', 'ItemName', 'CollectionName',
          'CollectionGenre', 'PostStatus', 'PostedDate', 'CollectionStatus', 'CollectedDate']


def row(url, status, date=''):
    return [url, 'shop', 'id', 'shop:id', '商品名', '', '', status, date, '未', '']


class FakeSheetsService:
    """GoogleSheetsManager が使う service.spreadsheets().values().get/update(...).execute() の偽物"""

    def __init__(self, values):
        self.values_data = values
        self.updates = []

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, spreadsheetId, range):
        return SimpleNamespace(execute=lambda: {'values': self.values_data})

    def update(self, spreadsheetId, range, valueInputOption, body):
        self.updates.append((range, body['values']))
        return SimpleNamespace(execute=lambda: {})


def test_get_unposted_items_returns_only_mi():
    service = FakeSheetsService([HEADER, row('u1', '済'), row('u2', '未'), row('u3', '不可'), row('u4', '未')])
    items = GoogleSheetsManager(service).get_unposted_items()
    assert [item['ItemURL'] for item in items] == ['u2', 'u4']


def test_get_unposted_items_missing_column():
    service = FakeSheetsService([HEADER[:-1], row('u1', '未')])
    assert GoogleSheetsManager(service).get_unposted_items() == []


def test_update_status_prefers_mi_row_when_url_is_duplicated():
    # 同じURLが2行ある場合、投稿対象として取得された「未」の行（3行目）を更新する
    service = FakeSheetsService([HEADER, row('dup', '不可', '2026-09-28'), row('dup', '未')])
    assert GoogleSheetsManager(service).update_post_status_by_url('dup', '済', '2026-10-12')
    assert service.updates == [(f"{config.SHEET_NAME}!H3:I3", [['済', '2026-10-12']])]


def test_update_status_falls_back_to_first_match():
    service = FakeSheetsService([HEADER, row('u1', '済'), row('u1', '不可')])
    assert GoogleSheetsManager(service).update_post_status_by_url('u1', '未', '')
    assert service.updates[0][0].endswith('H2:I2')


def test_update_status_url_not_found():
    service = FakeSheetsService([HEADER, row('u1', '未')])
    assert not GoogleSheetsManager(service).update_post_status_by_url('unknown', '済', '2026-10-12')
    assert service.updates == []


# ---------------------------------------------------------------------------
# ChatGPT（OpenAI API は偽物に置き換える）
# ---------------------------------------------------------------------------

def fake_openai(monkeypatch, content='紹介文です。', error=None):
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if error:
                raise error
            choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason='stop')
            return SimpleNamespace(choices=[choice])

    class FakeOpenAI:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(chatgpt_manager, 'OpenAI', FakeOpenAI)
    return calls


def test_gpt6_uses_max_completion_tokens_and_low_reasoning(monkeypatch):
    calls = fake_openai(monkeypatch)
    monkeypatch.setattr(chatgpt_manager, 'OPENAI_MODEL', 'gpt-6.1-sol')
    assert chatgpt_manager.generate_description('テスト商品') == '紹介文です。'
    params = calls[0]
    assert params['model'] == 'gpt-6.1-sol'
    # GPT-5/6系は max_tokens・temperature 非対応。reasoning_effort は none 非対応モデルがあるため low
    assert params['max_completion_tokens'] == 2000
    assert params['reasoning_effort'] == 'low'
    assert 'max_tokens' not in params and 'temperature' not in params


def test_gpt4_uses_temperature(monkeypatch):
    calls = fake_openai(monkeypatch)
    monkeypatch.setattr(chatgpt_manager, 'OPENAI_MODEL', 'gpt-4.1-mini')
    chatgpt_manager.generate_description('テスト商品')
    assert calls[0]['temperature'] == 0.7
    assert 'reasoning_effort' not in calls[0]


def test_description_strips_trailing_spaces(monkeypatch):
    # GPT-5.6系は行末にMarkdown改行用の半角スペース2つを付けて返すことがある
    fake_openai(monkeypatch, content='1行目。  \n2行目。  \n#楽天ROOM  ')
    assert chatgpt_manager.generate_description('テスト商品') == '1行目。\n2行目。\n#楽天ROOM'


def test_description_empty_or_error_returns_empty(monkeypatch):
    fake_openai(monkeypatch, content=None)
    assert chatgpt_manager.generate_description('テスト商品') == ''
    fake_openai(monkeypatch, error=RuntimeError('insufficient_quota'))
    assert chatgpt_manager.generate_description('テスト商品') == ''


# ---------------------------------------------------------------------------
# ログ
# ---------------------------------------------------------------------------

def test_get_logger_returns_shared_logger(log_to_tmp):
    assert logger_module.get_logger() is log_to_tmp
    logger_module.get_logger().error('テストのエラー')
    text = Path(log_to_tmp.log_file).read_text(encoding='utf-8')
    assert '[ERROR] テストのエラー' in text


def test_default_log_dir_is_app_dir():
    # 作業フォルダ（タスクスケジューラの「開始」設定）に左右されず、APP_DIR/logs に出力する
    default = logger_module.Logger.__init__.__defaults__[0]
    assert Path(default) == config.APP_DIR / 'logs'
