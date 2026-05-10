from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key
from app.dynamodb import chat_count_table
from app.config import settings

JST = timezone(timedelta(hours=9))


def _today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def _ttl_tomorrow_jst() -> int:
    now = datetime.now(JST)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(tomorrow.timestamp())


def get_chat_count(trial_uuid: str) -> int:
    today = _today_jst()
    response = chat_count_table.get_item(Key={"trial_uuid": trial_uuid, "date": today})
    item = response.get("Item")
    return int(item["count"]) if item else 0


def increment_chat_count(trial_uuid: str) -> int:
    today = _today_jst()
    response = chat_count_table.update_item(
        Key={"trial_uuid": trial_uuid, "date": today},
        UpdateExpression="SET #count = if_not_exists(#count, :zero) + :one, #ttl = :ttl",
        ExpressionAttributeNames={"#count": "count", "#ttl": "ttl"},
        ExpressionAttributeValues={
            ":zero": 0,
            ":one": 1,
            ":ttl": _ttl_tomorrow_jst(),
        },
        ReturnValues="UPDATED_NEW",
    )
    return int(response["Attributes"]["count"])


def is_limit_exceeded(trial_uuid: str) -> bool:
    return get_chat_count(trial_uuid) >= settings.trial_chat_limit
