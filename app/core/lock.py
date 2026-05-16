"""
Task lock manager.

現在はメモリ上のシンプルなロック管理。
Lambda本番移行時は RedisLock に差し替えるだけで動く設計にしておく。
"""

import asyncio
from typing import Dict

# Lambda本番では Redis に差し替える
# 例: lock_store = RedisLockStore(redis_url)
_locks: Dict[str, bool] = {}
_lock = asyncio.Lock()


async def acquire(task_name: str) -> bool:
    """
    タスクのロックを取得する。
    すでに実行中の場合は False を返す（二重起動防止）。
    """
    async with _lock:
        if _locks.get(task_name):
            return False
        _locks[task_name] = True
        return True


async def release(task_name: str) -> None:
    """タスクのロックを解放する。"""
    async with _lock:
        _locks[task_name] = False


def is_running(task_name: str) -> bool:
    """タスクが実行中かどうかを返す。"""
    return _locks.get(task_name, False)
