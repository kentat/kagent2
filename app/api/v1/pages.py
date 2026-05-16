"""
GET / — モック画面。

ステップ1: ボタン2つだけの最小構成。
ステップ2: kagent の漆黒・グラスモルフィズム UI を移植予定。
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["pages"])

_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>kagent2</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      min-height: 100svh;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 48px;
      background: #020617;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    h1 {
      font-size: 18px; font-weight: 700; letter-spacing: 0.1em;
      color: #10b981;
    }

    .actions {
      display: flex; flex-direction: column; gap: 16px;
      width: 100%; max-width: 320px;
    }

    button {
      width: 100%; padding: 16px;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      background: rgba(255,255,255,0.04);
      color: #f8fafc; font-size: 15px; font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    button:hover  { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.4); }
    button:active { background: rgba(16,185,129,0.2); }
    button:disabled { opacity: 0.4; cursor: not-allowed; }

    #toast {
      position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%);
      padding: 12px 24px; border-radius: 100px;
      font-size: 14px; font-weight: 600;
      opacity: 0; transition: opacity 0.3s;
      pointer-events: none; white-space: nowrap;
    }
    #toast.show { opacity: 1; }
    #toast.ok   { background: #10b981; color: #020617; }
    #toast.err  { background: #ef4444; color: #fff; }
    #toast.busy { background: #f59e0b; color: #020617; }
  </style>
</head>
<body>
  <h1>🏯 KAGENT 2</h1>

  <div class="actions">
    <button id="btn-collect" onclick="trigger('collect')">
      📡 Collect（STEVEデータ収集）
    </button>
    <button id="btn-morning" onclick="trigger('morning')">
      🌅 Morning（JOHNNYブリーフ配信）
    </button>
  </div>

  <div id="toast"></div>

  <script>
    async function trigger(action) {
      const btn = document.getElementById(`btn-${action}`);
      btn.disabled = true;

      try {
        const res = await fetch(`/api/v1/action/${action}`, { method: "POST" });
        const body = await res.json();

        if (res.ok) {
          showToast("✅ " + body.message, "ok");
        } else if (res.status === 409) {
          showToast("⚠️ " + (body.detail?.message ?? "実行中です"), "busy");
        } else {
          showToast("❌ エラーが発生しました", "err");
        }
      } catch (e) {
        showToast("❌ 通信エラー", "err");
      } finally {
        setTimeout(() => { btn.disabled = false; }, 3000);
      }
    }

    function showToast(msg, type) {
      const t = document.getElementById("toast");
      t.textContent = msg;
      t.className = `show ${type}`;
      setTimeout(() => { t.className = ""; }, 3500);
    }
  </script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    return HTMLResponse(_HTML)
