"""
kagent2 FastAPI アプリケーション。

設計方針:
  - Mangum でラップすることで Lambda + API Gateway に即移植可能
  - ローカル / Railway では uvicorn で直接起動
  - 全エンドポイントはステートレスに設計する
"""

import logging

from fastapi import FastAPI
from mangum import Mangum

from app.api.v1.actions import router as actions_router
from app.api.v1.pages import router as pages_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="kagent2",
    description="けんたのパーソナルAI秘書システム（第2世代）",
    version="2.0.0",
)

app.include_router(pages_router)
app.include_router(actions_router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "2.0.0"}


# Lambda ハンドラー（ローカルでは uvicorn が直接 app を参照する）
handler = Mangum(app, lifespan="off")
