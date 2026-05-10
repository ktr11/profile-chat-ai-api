"""DynamoDB Local にテーブルを作成するスクリプト。"""
import boto3

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-northeast-1",
    endpoint_url="http://localhost:8000",
)

dynamodb.create_table(
    TableName="dev-user_chat_count",
    KeySchema=[
        {"AttributeName": "trial_uuid", "KeyType": "HASH"},
        {"AttributeName": "date", "KeyType": "RANGE"},
    ],
    AttributeDefinitions=[
        {"AttributeName": "trial_uuid", "AttributeType": "S"},
        {"AttributeName": "date", "AttributeType": "S"},
    ],
    BillingMode="PAY_PER_REQUEST",
)
print("Created: dev-user_chat_count")

dynamodb.create_table(
    TableName="dev-user_chat_history",
    KeySchema=[
        {"AttributeName": "trial_uuid", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"},
    ],
    AttributeDefinitions=[
        {"AttributeName": "trial_uuid", "AttributeType": "S"},
        {"AttributeName": "timestamp", "AttributeType": "N"},
    ],
    BillingMode="PAY_PER_REQUEST",
)
print("Created: dev-user_chat_history")
