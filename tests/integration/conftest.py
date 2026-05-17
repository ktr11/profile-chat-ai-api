import boto3
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

DYNAMODB_ENDPOINT = "http://localhost:8000"

TABLE_CONFIGS = [
    {
        "TableName": "dev-user_chat_count",
        "KeySchema": [
            {"AttributeName": "trial_uuid", "KeyType": "HASH"},
            {"AttributeName": "date", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "trial_uuid", "AttributeType": "S"},
            {"AttributeName": "date", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "dev-user_chat_history",
        "KeySchema": [
            {"AttributeName": "trial_uuid", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "trial_uuid", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


@pytest.fixture(scope="session")
def dynamodb_local():
    """DynamoDB Localに接続し、テーブルを作成する。セッション終了時に削除する。"""
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="ap-northeast-1",
        endpoint_url=DYNAMODB_ENDPOINT,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    # 既存テーブルを削除（前回のテスト実行が途中終了した場合の対処）
    for config in TABLE_CONFIGS:
        try:
            dynamodb.Table(config["TableName"]).delete()
        except dynamodb.meta.client.exceptions.ResourceNotFoundException:
            pass

    created_tables = []
    for config in TABLE_CONFIGS:
        table = dynamodb.create_table(**config)
        table.wait_until_exists()
        created_tables.append(table)

    yield dynamodb

    for table in created_tables:
        table.delete()


@pytest.fixture(scope="function")
def db(dynamodb_local):
    """各テストにDynamoDBリソースとテーブル参照を提供し、モジュールレベルの参照を差し替える。"""
    count_table = dynamodb_local.Table("dev-user_chat_count")
    history_table = dynamodb_local.Table("dev-user_chat_history")

    with (
        patch("app.dynamodb.chat_count_table", count_table),
        patch("app.dynamodb.chat_history_table", history_table),
        patch("app.services.chat_count.chat_count_table", count_table),
        patch("app.services.chat_history.chat_history_table", history_table),
    ):
        yield {"count_table": count_table, "history_table": history_table}


@pytest.fixture(scope="function")
def client(db):
    """DynamoDB Local接続済みのFastAPI TestClientを返す。"""
    from app.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
