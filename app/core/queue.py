"""
Queue abstraction layer.

ローカル/Railway : BackgroundTasks でインプロセス非同期実行
Lambda 本番      : SQS にメッセージを投げて別 Lambda を起動

差し替えは QUEUE_BACKEND 環境変数で切り替える（将来）。
現時点はすべて LocalQueue。
"""

import asyncio
import logging
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
    Lambda 本番用 SQS キュー（未実装・将来のプレースホルダー）。

    実装時は boto3 で SQS にメッセージを投げ、
    別の Lambda 関数がトリガーされてタスクを実行する。
    """

    def __init__(self, queue_url: str):
        self.queue_url = queue_url

    async def enqueue(
        self,
        background_tasks: BackgroundTasks,
        task_fn: Callable[[], Awaitable[None]],
        task_name: str,
    ) -> None:
        raise NotImplementedError(
            "SQSQueue は未実装です。Lambda 移行フェーズで実装してください。"
        )


# アプリ全体で使うキューインスタンス
# 将来: os.getenv("QUEUE_BACKEND") == "sqs" なら SQSQueue を返す
def get_queue() -> LocalQueue:
    return LocalQueue()
