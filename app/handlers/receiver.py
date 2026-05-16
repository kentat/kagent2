"""
kagent2 / Receiver Lambda

役割:
  Telegram Webhook を受信し、SQS にメッセージをエンキューして即座に 200 を返す。
  重い処理は Worker Lambda に委譲する。

環境変数:
  SQS_QUEUE_URL  例: https://sqs.ap-northeast-1.amazonaws.com/123456789012/kagent2-queue
"""

import json
import os
from typing import Any

import boto3

# ウォームスタート時に再利用される（毎リクエストの生成コストを省く）
_sqs = boto3.client("sqs", region_name="ap-northeast-1")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    queue_url = os.environ.get("SQS_QUEUE_URL", "")
    if not queue_url:
        print("[ERROR] SQS_QUEUE_URL が設定されていません")
        return {"statusCode": 500, "body": "queue url missing"}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        print("[WARN] body のパースに失敗")
        return {"statusCode": 400, "body": "bad request"}

    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text    = message.get("text", "")

    if not chat_id or not text:
        return {"statusCode": 200, "body": "ok"}

    payload = json.dumps({"chat_id": chat_id, "text": text})
    print(f"[RECV] chat_id={chat_id} text={text!r} → SQS enqueue")
    _sqs.send_message(QueueUrl=queue_url, MessageBody=payload)

    return {"statusCode": 200, "body": "ok"}
