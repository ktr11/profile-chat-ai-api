# profile-chat-ai-api

試用ユーザーがAIとチャットするためのバックエンドAPI。HTTPOnlyクッキー（`trial_uuid`）によるセッション管理と、1日あたりのチャット回数制限を実装しています。

## 概要

- FastAPI + DynamoDB によるRESTful API
- セッションごとに1日あたりのチャット上限（デフォルト: 5回）を管理
- チャット履歴をDynamoDBに保存し、コンテキストとしてLLMに渡す
- **LLM統合は未実装（TODO）** — 現在AIレスポンスはスタブです

## 前提条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker（DynamoDB Local の起動に使用）

## はじめに

```bash
# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env

# DynamoDB Local の起動
docker-compose up -d

# DynamoDB テーブルの作成
uv run python scripts/create_local_tables.py

# 開発サーバーの起動
uv run uvicorn app.main:app --reload
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|---|---|---|
| `CHAT_COUNT_TABLE_NAME` | チャット回数管理テーブル名 | — |
| `CHAT_HISTORY_TABLE_NAME` | チャット履歴テーブル名 | — |
| `TRIAL_CHAT_LIMIT` | 1日あたりのチャット上限 | `5` |
| `CHAT_HISTORY_LIMIT` | LLMに渡す直近の履歴件数 | `10` |
| `DYNAMODB_ENDPOINT_URL` | DynamoDBエンドポイント（ローカル開発時） | `http://localhost:8000` |

## APIエンドポイント

詳細は [`docs/openapi.json`](docs/openapi.json) を参照してください。

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| POST | `/session` | セッション開始。`trial_uuid` クッキーを発行し、チャット回数を返す |
| POST | `/chat` | メッセージ送信。クッキーがない場合は401、上限超過で403 |

## テスト実行

```bash
uv run pytest
```

## ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [OpenAPI 仕様](./docs/openapi.json) | API エンドポイント定義 |
| [システム全体構成](https://github.com/ktr11/profile-chat-ai-docs/blob/main/docs/architecture/overall.md) | プロジェクト横断のアーキテクチャ図 |
