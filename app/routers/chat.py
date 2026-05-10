import uuid
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel
from app.services import chat_count, chat_history, llm
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

COOKIE_NAME = "trial_uuid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    remaining: int


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


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    response: Response,
    trial_uuid: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    uid = _get_or_create_uuid(response, trial_uuid)

    if chat_count.is_limit_exceeded(uid):
        raise HTTPException(status_code=403, detail="本日のチャット上限に達しました。")

    history = chat_history.get_recent_history(uid)
    reply = llm.invoke_chat(history, body.message)

    chat_history.save_message(uid, "user", body.message)
    chat_history.save_message(uid, "assistant", reply)

    count = chat_count.increment_chat_count(uid)
    remaining = max(0, settings.trial_chat_limit - count)

    return ChatResponse(reply=reply, remaining=remaining)
