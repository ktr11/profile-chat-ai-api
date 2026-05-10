from fastapi import FastAPI
from app.routers import chat

app = FastAPI(title="profile-chat-ai-api")

app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
