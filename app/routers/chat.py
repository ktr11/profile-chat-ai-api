from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field
from app.services import chat_count, chat_history, llm
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

COOKIE_NAME = "trial_uuid"


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="ユーザーが送信するメッセージ",
        examples=["自己紹介してください"],
    )


class ChatResponse(BaseModel):
    reply: str = Field(
        ...,
        description="AIからの返答テキスト",
        examples=["はじめまして！私はプロフィールチャットAIです。"],
    )
    chat_count: int = Field(
        ...,
        description="本日の送信回数（今回のメッセージを含む）",
        examples=[3],
    )
    chat_limit: int = Field(
        ...,
        description="1日の送信上限回数",
        examples=[5],
    )


@router.post(
    "",
    response_model=ChatResponse,
    summary="チャットメッセージを送信する",
    description=(
        "ユーザーのメッセージをAIに送信し、返答と送信回数情報を返す。\n\n"
        "**前提条件:**\n"
        "- 事前に `POST /session` を呼び出して `trial_uuid` クッキーを取得しておく必要がある。\n"
        "- クッキーが存在しない場合は `401 Unauthorized` を返す。\n\n"
        "**チャット制限:**\n"
        "- 1日あたりの上限に達した場合は `403 Forbidden` を返す。"
    ),
    responses={
        200: {
            "description": "AIの返答と送信回数情報",
            "content": {
                "application/json": {
                    "example": {
                        "reply": "はじめまして！私はプロフィールチャットAIです。何でも聞いてください。",
                        "chat_count": 3,
                        "chat_limit": 5,
                    }
                }
            },
        },
        401: {
            "description": "セッションが開始されていない（trial_uuid クッキーなし）",
            "content": {
                "application/json": {
                    "example": {"detail": "セッションが開始されていません。"}
                }
            },
        },
        403: {
            "description": "本日のチャット上限に達した",
            "content": {
                "application/json": {
                    "example": {"detail": "本日のチャット上限に達しました。"}
                }
            },
        },
        422: {
            "description": "バリデーションエラー（リクエストボディの形式が不正）",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["body", "message"],
                                "msg": "Field required",
                            }
                        ]
                    }
                }
            },
        },
    },
)
def post_chat(
    body: ChatRequest,
    trial_uuid: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
        description="トライアルユーザーを識別するUUID。POST /session で発行される。",
    ),
):
    if not trial_uuid:
        raise HTTPException(status_code=401, detail="セッションが開始されていません。")

    uid = trial_uuid

    if chat_count.is_limit_exceeded(uid):
        raise HTTPException(status_code=403, detail="本日のチャット上限に達しました。")

    history = chat_history.get_recent_history(uid)
    reply = llm.invoke_chat(history, body.message)

    chat_history.save_message(uid, "user", body.message)
    chat_history.save_message(uid, "assistant", reply)

    count = chat_count.increment_chat_count(uid)

    return ChatResponse(reply=reply, chat_count=count, chat_limit=settings.trial_chat_limit)
