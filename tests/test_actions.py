"""
kagent2 PoC テスト。

カバー範囲:
  - /health エンドポイント
  - /api/v1/action/collect の正常系・二重起動防止
  - /api/v1/action/morning の正常系・二重起動防止
  - /api/v1/action/status の返却形式
"""

import pytest
from fastapi.testclient import TestClient

from app.core import lock
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_locks():
    """各テスト前後にロック状態をリセットする。"""
    lock._locks.clear()
    yield
    lock._locks.clear()


# ─── ヘルスチェック ──────────────────────────────────────────────

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ─── /collect ───────────────────────────────────────────────────

def test_collect_accepted():
    res = client.post("/api/v1/action/collect")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["task"] == "collect"


def test_collect_double_trigger_returns_409():
    # TestClient は BackgroundTasks を同期実行するためタスク完了後にロックが解放される。
    # そのため、ロックを直接注入してから2回目のリクエストを送る。
    lock._locks["collect"] = True
    res = client.post("/api/v1/action/collect")
    assert res.status_code == 409
    assert res.json()["detail"]["status"] == "running"


# ─── /morning ───────────────────────────────────────────────────

def test_morning_accepted():
    res = client.post("/api/v1/action/morning")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "accepted"
    assert body["task"] == "morning"


def test_morning_double_trigger_returns_409():
    lock._locks["morning"] = True
    res = client.post("/api/v1/action/morning")
    assert res.status_code == 409
    assert res.json()["detail"]["status"] == "running"


# ─── collect と morning は独立したロック ────────────────────────

def test_collect_and_morning_independent():
    """collect 実行中でも morning は受け付ける（ロックは独立）。"""
    r1 = client.post("/api/v1/action/collect")
    r2 = client.post("/api/v1/action/morning")
    assert r1.status_code == 200
    assert r2.status_code == 200


# ─── /status ────────────────────────────────────────────────────

def test_status_initial():
    res = client.get("/api/v1/action/status")
    assert res.status_code == 200
    body = res.json()
    assert body["collect"] is False
    assert body["morning"] is False


def test_status_after_collect():
    lock._locks["collect"] = True
    res = client.get("/api/v1/action/status")
    assert res.json()["collect"] is True
    assert res.json()["morning"] is False
