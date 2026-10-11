"""テスト共通の設定"""
import pytest

import logger as logger_module
import rakuten_login
from tests.fake_rakuten import CORRECT_PASSWORD


@pytest.fixture(autouse=True)
def log_to_tmp(tmp_path, monkeypatch):
    """テスト中のログは一時フォルダに出力する（プロジェクトの logs を汚さない）"""
    test_logger = logger_module.Logger(str(tmp_path / "logs"))
    monkeypatch.setattr(logger_module, "_shared_logger", test_logger)
    return test_logger


@pytest.fixture
def credentials(monkeypatch):
    """テスト用の楽天ログイン情報（.env は使わない）"""
    monkeypatch.setattr(rakuten_login, "RAKUTEN_USER_ID", "user@example.com")
    monkeypatch.setattr(rakuten_login, "RAKUTEN_PASSWORD", CORRECT_PASSWORD)

