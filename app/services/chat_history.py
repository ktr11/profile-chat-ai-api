import time
from boto3.dynamodb.conditions import Key
from app.dynamodb import chat_history_table
from app.config import settings


def get_recent_history(trial_uuid: str) -> list[dict]:
    response = chat_history_table.query(
        KeyConditionExpression=Key("trial_uuid").eq(trial_uuid),
        ScanIndexForward=False,
        Limit=settings.chat_history_limit,
    )
    items = response.get("Items", [])
    items.sort(key=lambda x: x["timestamp"])
    return [{"role": item["role"], "content": item["message"]} for item in items]


def save_message(trial_uuid: str, role: str, message: str) -> None:
    chat_history_table.put_item(
        Item={
            "trial_uuid": trial_uuid,
            "timestamp": int(time.time() * 1000),
            "role": role,
            "message": message,
        }
    )
