from fastapi import FastAPI
from app.routers import chat

app = FastAPI(
    title="profile-chat-ai-api",
    description=(
        "プロフィールチャットAIのバックエンドAPI。\n\n"
        "トライアルユーザーがAIとチャットするためのエンドポイントを提供する。\n"
        "セッション管理にはHTTPOnly クッキー（`trial_uuid`）を使用し、"
        "チャット回数の制限はDynamoDBで管理される（JST基準で1日ごとにリセット）。"
    ),
    version="0.1.0",
)

app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
