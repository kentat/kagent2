# kagent2

けんたのパーソナルAI秘書システム 第2世代。

## アーキテクチャ方針

- **完全ステートレス** — AWS Lambda への移植を前提に設計
- **非同期イベント駆動** — ボタン押下は即座に `accepted` を返し、重い処理はバックグラウンドへ
- **二重起動防止** — ロックはメモリ（PoC）→ Redis（本番）に差し替え可能

## ディレクトリ構成

```
kagent2/
├── app/
│   ├── main.py               # FastAPI + Mangum（Lambda対応）
│   ├── api/v1/
│   │   └── actions.py        # POST /api/v1/action/{collect,morning}
│   └── core/
│       └── lock.py           # タスクロック管理（Redis差し替え可）
├── tests/
│   └── test_actions.py       # 8テストケース
├── requirements.txt
└── README.md
```

## エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | `/health` | ヘルスチェック |
| POST | `/api/v1/action/collect` | STEVEデータ収集キック |
| POST | `/api/v1/action/morning` | JOHNNYモーニングブリーフキック |
| GET | `/api/v1/action/status` | タスク実行状態確認 |

## ローカル起動

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## テスト

```bash
pytest tests/ -v
```

## Lambda 移行時の注意点

`BackgroundTasks` は Lambda 環境では動作しない（レスポンス返却後にプロセスが終了するため）。
本番移行時は以下に差し替える：

- `BackgroundTasks` → SQS キック → 別 Lambda 実行
- `lock.py` のメモリロック → Redis ロック（Upstash）
