import uuid
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, Field
from app.services import chat_count, chat_history, llm
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

COOKIE_NAME = "trial_uuid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


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


def _get_or_create_uuid(response: Response, trial_uuid: str | None) -> str:
    if trial_uuid:
        return trial_uuid
    new_uuid = str(uuid.uuid4())
    response.set_cookie(
        key=COOKIE_NAME,
        value=new_uuid,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
    )
    return new_uuid


@router.post(
    "",
    response_model=ChatResponse,
    summary="チャットメッセージを送信する",
    description=(
        "ユーザーのメッセージをAIに送信し、返答と送信回数情報を返す。\n\n"
        "**トライアルセッション管理:**\n"
        "- リクエストに `trial_uuid` クッキーが含まれていない場合、新規UUIDを発行して `Set-Cookie` ヘッダーで返す。\n"
        "- 発行されたUUIDはDynamoDBで1日あたりのチャット回数管理に使用される（JST基準でリセット）。\n\n"
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
    response: Response,
    trial_uuid: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
        description="トライアルユーザーを識別するUUID。未設定の場合は自動発行される。",
    ),
):
    uid = _get_or_create_uuid(response, trial_uuid)

    if chat_count.is_limit_exceeded(uid):
        raise HTTPException(status_code=403, detail="本日のチャット上限に達しました。")

    history = chat_history.get_recent_history(uid)
    reply = llm.invoke_chat(history, body.message)

    chat_history.save_message(uid, "user", body.message)
    chat_history.save_message(uid, "assistant", reply)

    count = chat_count.increment_chat_count(uid)

    return ChatResponse(reply=reply, chat_count=count, chat_limit=settings.trial_chat_limit)
