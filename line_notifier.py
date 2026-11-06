"""
LINE通知モジュール - 投稿結果をLINEに送信する

LINE Messaging API のプッシュメッセージで、LINE公式アカウントから自分のLINEに通知します。
（LINE Notify は2025年3月31日にサービスが終了したため使用しません）

.env の LINE_CHANNEL_ACCESS_TOKEN と LINE_USER_ID が未設定の場合は通知しません。
通知に失敗しても投稿処理には影響させません（ログに記録するのみ）。
"""
import json
import urllib.error
import urllib.request
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
from logger import get_logger

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
MESSAGE_TITLE = "【楽天ROOM自動投稿】"
MAX_TEXT_LENGTH = 5000  # LINEのテキストメッセージの上限文字数


def is_line_enabled() -> bool:
    """LINE通知の設定がされているか"""
    return bool(LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID)


def send_line_message(text: str) -> bool:
    """
    LINEにテキストメッセージを送信する

    Args:
        text: 送信する本文（先頭に「【楽天ROOM自動投稿】」を付けて送る）

    Returns:
        bool: 送信できればTrue（未設定・失敗時はFalse）
    """
    if not is_line_enabled():
        return False

    message = f"{MESSAGE_TITLE}\n{text}"[:MAX_TEXT_LENGTH]
    body = json.dumps({
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }).encode("utf-8")
    request = urllib.request.Request(
        LINE_PUSH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15):
            pass
        get_logger().info("LINEに投稿結果を通知しました")
        return True
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        get_logger().error(f"LINEへの通知に失敗しました（HTTP {e.code}）: {detail}")
    except Exception as e:
        get_logger().error(f"LINEへの通知に失敗しました: {e}")
    return False
