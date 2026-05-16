"""
kagent2 / AWS Lambda エントリーポイント

役割:
  Telegram Webhook を受け取り、受信したテキストをそのまま送り返す（オウム返し）。
  依存ライブラリなし — 標準の urllib のみで動作する。

環境変数:
  TELEGRAM_BOT_TOKEN  例: 123456:ABC-DEF...

Webhook 設定 URL（デプロイ後に1回叩く）:
  https://api.telegram.org/bot<TOKEN>/setWebhook?url=<API_GATEWAY_URL>
"""

import json
import os
import urllib.request
from typing import Any


# ─── Telegram API 呼び出し ──────────────────────────────────────

def send_message(telegram_api: str, chat_id: int, text: str) -> None:
    """Telegram に sendMessage リクエストを送る。"""
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
    }).encode("utf-8")

    req = urllib.request.Request(
        url=f"{telegram_api}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())


# ─── Lambda ハンドラー ──────────────────────────────────────────

def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    API Gateway から呼ばれる Lambda ハンドラー。

    Telegram が送ってくる Webhook は event["body"] に JSON 文字列として入る。
    メッセージを受け取ってそのままオウム返しする。
    """
    # ── 環境変数チェック ──────────────────────────────────────
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN が設定されていません")
        return {"statusCode": 500, "body": "token missing"}

    telegram_api = f"https://api.telegram.org/bot{token}"

    # ── ボディのパース ────────────────────────────────────────
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        print("[WARN] body のパースに失敗")
        return {"statusCode": 400, "body": "bad request"}

    # ── メッセージの取り出し ──────────────────────────────────
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text    = message.get("text", "")

    if not chat_id or not text:
        # コマンド以外（スタンプ・写真等）は無視して 200 を返す
        return {"statusCode": 200, "body": "ok"}

    # ── オウム返し ────────────────────────────────────────────
    print(f"[MSG] chat_id={chat_id} text={text!r}")
    send_message(telegram_api, chat_id, f"🦜 {text}")

    return {"statusCode": 200, "body": "ok"}
