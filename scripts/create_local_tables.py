"""DynamoDB Local にテーブルを作成するスクリプト。"""
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-northeast-1",
    endpoint_url="http://localhost:8000",
)

TABLES = [
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

for table_def in TABLES:
    name = table_def["TableName"]
    try:
        dynamodb.create_table(**table_def)
        print(f"Created: {name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Already exists (skipped): {name}")
        else:
            raise
