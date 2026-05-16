"""
POST /api/v1/action/* エンドポイント群。

設計方針:
  - リクエストを受けたら即座に {"status": "accepted"} を返す
  - 重い処理は queue.enqueue() 経由で非同期実行
  - lock.py で二重起動をガード
  - Lambda 本番移行時は queue.py の実装を SQS に差し替えるだけ
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core import lock
from app.core.queue import get_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/action", tags=["action"])
queue  = get_queue()


# ─── レスポンスモデル ────────────────────────────────────────────

class AcceptedResponse(BaseModel):
    status: str = "accepted"
    message: str
    task: str


class RejectedResponse(BaseModel):
    status: str = "running"
    message: str
    task: str


# ─── ダミータスク（PoC用）────────────────────────────────────────

async def _dummy_collect() -> None:
    task_name = "collect"
    try:
        logger.info("[STEVE] データ収集開始")
        await asyncio.sleep(10)
        logger.info("[STEVE] データ収集完了 → Redis 保存")
    except Exception as e:
        logger.error(f"[STEVE] エラー: {e}")
    finally:
        await lock.release(task_name)


async def _dummy_morning() -> None:
    task_name = "morning"
    try:
        logger.info("[JOHNNY] モーニングブリーフ生成開始")
        await asyncio.sleep(10)
        logger.info("[JOHNNY] 整形完了 → Web キャッシュ更新")
    except Exception as e:
        logger.error(f"[JOHNNY] エラー: {e}")
    finally:
        await lock.release(task_name)


# ─── エンドポイント ──────────────────────────────────────────────

@router.post(
    "/collect",
    response_model=AcceptedResponse,
    responses={409: {"model": RejectedResponse}},
    summary="手動データ収集トリガー（STEVE 相当）",
)
async def trigger_collect(background_tasks: BackgroundTasks):
    task_name = "collect"
    if not await lock.acquire(task_name):
        raise HTTPException(
            status_code=409,
            detail=RejectedResponse(
                message="collect タスクはすでに実行中です",
                task=task_name,
            ).model_dump(),
        )
    await queue.enqueue(background_tasks, _dummy_collect, task_name)
    return AcceptedResponse(message="データ収集タスクを受け付けました", task=task_name)


@router.post(
    "/morning",
    response_model=AcceptedResponse,
    responses={409: {"model": RejectedResponse}},
    summary="モーニングブリーフ配信トリガー（JOHNNY 相当）",
)
async def trigger_morning(background_tasks: BackgroundTasks):
    task_name = "morning"
    if not await lock.acquire(task_name):
        raise HTTPException(
            status_code=409,
            detail=RejectedResponse(
                message="morning タスクはすでに実行中です",
                task=task_name,
            ).model_dump(),
        )
    await queue.enqueue(background_tasks, _dummy_morning, task_name)
    return AcceptedResponse(message="モーニングブリーフタスクを受け付けました", task=task_name)


@router.get("/status", summary="タスク実行状態の確認（デバッグ用）")
async def get_status():
    return {
        "collect": lock.is_running("collect"),
        "morning": lock.is_running("morning"),
    }
