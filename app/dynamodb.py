import boto3
from app.config import settings


def get_dynamodb_resource():
    kwargs = {}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)


dynamodb = get_dynamodb_resource()
chat_count_table = dynamodb.Table(settings.chat_count_table_name)
chat_history_table = dynamodb.Table(settings.chat_history_table_name)
