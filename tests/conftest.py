import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from unittest.mock import patch

# .envのテーブル名と一致させる（pydantic-settingsが.envを読むため）
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


@pytest.fixture(scope="function")
def aws_mock():
    """motoでAWS環境をモックし、テスト用DynamoDBテーブルを作成する。

    importlib.reload()は使わず、patch()でモジュールレベルのテーブル参照を
    直接差し替える。各テストは独立したmotoコンテキスト（空のDB状態）で実行される。
    """
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        for config in TABLE_CONFIGS:
            dynamodb.create_table(**config)

        count_table = dynamodb.Table("dev-user_chat_count")
        history_table = dynamodb.Table("dev-user_chat_history")

        with (
            patch("app.dynamodb.chat_count_table", count_table),
            patch("app.dynamodb.chat_history_table", history_table),
            patch("app.services.chat_count.chat_count_table", count_table),
            patch("app.services.chat_history.chat_history_table", history_table),
        ):
            yield dynamodb


@pytest.fixture(scope="function")
def client(aws_mock):
    """DynamoDBモック済みのFastAPI TestClientを返す。"""
    from app.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
