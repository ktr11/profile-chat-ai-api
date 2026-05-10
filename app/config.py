from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class Settings(BaseSettings):
    chat_count_table_name: str
    chat_history_table_name: str
    trial_chat_limit: int = 5
    chat_history_limit: int = 10
    dynamodb_endpoint_url: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
