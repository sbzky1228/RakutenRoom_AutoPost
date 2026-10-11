"""
ロギングモジュール - ログ出力機能
"""
import datetime
import os
from config import APP_DIR


class Logger:
    """ログ出力を管理するクラス"""
    
    def __init__(self, log_dir: str = str(APP_DIR / 'logs')):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # ログファイル名
        now = datetime.datetime.now()
        self.log_file = os.path.join(
            log_dir,
            f"rakuten_room_{now.strftime('%Y%m%d_%H%M%S')}.log"
        )
    
    def log(self, message: str, level: str = 'INFO'):
        """
        ログを出力
        
        Args:
            message: ログメッセージ
            level: ログレベル（INFO, WARNING, ERROR）
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def info(self, message: str):
        """INFO レベルでログ出力"""
        self.log(message, 'INFO')
    
    def warning(self, message: str):
        """WARNING レベルでログ出力"""
        self.log(message, 'WARNING')
    
    def error(self, message: str):
        """ERROR レベルでログ出力"""
        self.log(message, 'ERROR')


_shared_logger = None


def get_logger() -> Logger:
    """プログラム全体で共有するLoggerを取得する（初回呼び出し時に1つだけ作成し、同じログファイルに出力する）"""
    global _shared_logger
    if _shared_logger is None:
        _shared_logger = Logger()
    return _shared_logger
