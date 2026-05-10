import uuid
from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel, Field
from app.services import chat_count
from app.config import settings

router = APIRouter(prefix="/session", tags=["session"])

COOKIE_NAME = "trial_uuid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


class SessionResponse(BaseModel):
    chat_count: int = Field(
        ...,
        description="本日の送信回数",
        examples=[0],
    )
    chat_limit: int = Field(
        ...,
        description="1日の送信上限回数",
        examples=[5],
    )


@router.post(
    "",
    response_model=SessionResponse,
    summary="チャットセッションを開始する",
    description=(
        "チャット利用開始時に呼び出す。`trial_uuid` クッキーを発行し、本日の送信回数と上限を返す。\n\n"
        "既にクッキーが存在する場合はそのまま使用し、現在のカウントを返す。"
    ),
    responses={
        200: {
            "description": "セッション情報（送信回数と上限）",
            "content": {
                "application/json": {
                    "example": {
                        "chat_count": 0,
                        "chat_limit": 5,
                    }
                }
            },
        },
    },
)
def post_session(
    response: Response,
    trial_uuid: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
        description="トライアルユーザーを識別するUUID。未設定の場合は自動発行される。",
    ),
):
    if trial_uuid:
        uid = trial_uuid
    else:
        uid = str(uuid.uuid4())
        response.set_cookie(
            key=COOKIE_NAME,
            value=uid,
            httponly=True,
            max_age=COOKIE_MAX_AGE,
            samesite="lax",
        )

    count = chat_count.get_chat_count(uid)
    return SessionResponse(chat_count=count, chat_limit=settings.trial_chat_limit)
