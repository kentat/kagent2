"""
kagent2 / Worker Lambda

役割:
  SQS トリガーで起動し、キュー内のメッセージを処理する。
  現在はオウム返し。将来は portfolio.py / market.py のロジックをここに追加する。

環境変数:
  TELEGRAM_BOT_TOKEN  例: 123456:ABC-DEF...

SQS メッセージ形式:
  {"chat_id": <int>, "text": "<str>"}
"""

import json
import os
import urllib.request
from typing import Any


def _send_message(telegram_api: str, chat_id: int, text: str) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url=f"{telegram_api}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN が設定されていません")
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")  # SQS に再試行させる

    telegram_api = f"https://api.telegram.org/bot{token}"

    for record in event.get("Records", []):
        try:
            payload = json.loads(record["body"])
            chat_id = payload["chat_id"]
            text    = payload["text"]
            print(f"[WORK] chat_id={chat_id} text={text!r}")

            # ── ここに将来のロジックを追加する ──────────────────────
            # if text.startswith("/portfolio"): handle_portfolio(chat_id)
            # if text.startswith("/market"):    handle_market(chat_id)
            # ────────────────────────────────────────────────────────

            _send_message(telegram_api, chat_id, f"🦜 {text}")
        except Exception as e:
            print(f"[ERROR] レコード処理失敗: {e}")
            raise  # SQS の再試行 / DLQ に委譲

    return {"statusCode": 200, "body": "ok"}
