"""
Queue abstraction layer.

ローカル/Railway : BackgroundTasks でインプロセス非同期実行
Lambda 本番      : SQS にメッセージを投げて Worker Lambda を起動

切り替えは SQS_QUEUE_URL 環境変数の有無で自動判定する。
"""

import json
import logging
import os
from typing import Callable, Awaitable

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class LocalQueue:
    """
    開発・Railway 用インメモリキュー。
    FastAPI の BackgroundTasks に委譲するだけ。

    NOTE: Lambda + Mangum では BackgroundTasks はレスポンス返却後に
    プロセスが終了するため動作しない。
    本番 Lambda 移行時は SQSQueue に差し替えること。
    """

    async def enqueue(
        self,
        background_tasks: BackgroundTasks,
        task_fn: Callable[[], Awaitable[None]],
        task_name: str,
    ) -> None:
        logger.info(f"[LocalQueue] enqueue: {task_name}")
        background_tasks.add_task(task_fn)


class SQSQueue:
    """
    Lambda 本番用 SQS キュー。
    タスク名を SQS に投げ、Worker Lambda がそれを受けて実行する。
    """

    def __init__(self, queue_url: str) -> None:
        import boto3
        self.queue_url = queue_url
        self._client = boto3.client("sqs", region_name="ap-northeast-1")

    async def enqueue(
        self,
        background_tasks: BackgroundTasks,
        task_fn: Callable[[], Awaitable[None]],
        task_name: str,
    ) -> None:
        logger.info(f"[SQSQueue] enqueue: {task_name}")
        self._client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps({"task": task_name}),
        )


def get_queue() -> LocalQueue | SQSQueue:
    """SQS_QUEUE_URL が設定されていれば SQSQueue、なければ LocalQueue を返す。"""
    queue_url = os.environ.get("SQS_QUEUE_URL", "")
    if queue_url:
        return SQSQueue(queue_url)
    return LocalQueue()
