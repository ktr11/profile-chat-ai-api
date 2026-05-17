from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

JST = timezone(timedelta(hours=9))


@pytest.fixture(autouse=True)
def setup(aws_mock):
    pass


class TestGetChatCount:
    def test_new_user_returns_zero(self):
        """未登録ユーザーのカウントは0を返す。"""
        from app.services.chat_count import get_chat_count

        assert get_chat_count("user-new") == 0

    def test_returns_count_after_increment(self):
        """インクリメント後にカウントが1増えていることを確認する。"""
        from app.services.chat_count import get_chat_count, increment_chat_count

        increment_chat_count("user-abc")
        assert get_chat_count("user-abc") == 1

    def test_different_users_are_isolated(self):
        """異なるユーザーのカウントは互いに独立している。"""
        from app.services.chat_count import get_chat_count, increment_chat_count

        increment_chat_count("user-1")
        increment_chat_count("user-1")
        increment_chat_count("user-2")

        assert get_chat_count("user-1") == 2
        assert get_chat_count("user-2") == 1


class TestIncrementChatCount:
    def test_first_increment_returns_one(self):
        """初回インクリメントは1を返す。"""
        from app.services.chat_count import increment_chat_count

        assert increment_chat_count("user-x") == 1

    def test_subsequent_increments_accumulate(self):
        """複数回インクリメントすると累積した値を返す。"""
        from app.services.chat_count import increment_chat_count

        increment_chat_count("user-y")
        increment_chat_count("user-y")
        result = increment_chat_count("user-y")

        assert result == 3

    def test_ttl_is_set_to_tomorrow_jst(self):
        """TTLが翌日0時（JST）のUNIXタイムスタンプに設定される。"""
        from app.services.chat_count import increment_chat_count
        import app.dynamodb as ddb

        today = datetime.now(JST).strftime("%Y-%m-%d")
        increment_chat_count("user-ttl")

        item = ddb.chat_count_table.get_item(
            Key={"trial_uuid": "user-ttl", "date": today}
        )["Item"]

        tomorrow_start = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        assert item["ttl"] == int(tomorrow_start.timestamp())


class TestIsLimitExceeded:
    def test_under_limit_returns_false(self):
        """上限未満（4回）では制限超過と判定されない。"""
        from app.services.chat_count import is_limit_exceeded, increment_chat_count

        for _ in range(4):
            increment_chat_count("user-under")

        assert is_limit_exceeded("user-under") is False

    def test_at_limit_returns_true(self):
        """ちょうど上限（5回）に達すると制限超過と判定される。"""
        from app.services.chat_count import is_limit_exceeded, increment_chat_count

        for _ in range(5):
            increment_chat_count("user-at")

        assert is_limit_exceeded("user-at") is True

    def test_over_limit_returns_true(self):
        """上限を超えた（6回）場合も制限超過と判定される。"""
        from app.services.chat_count import is_limit_exceeded, increment_chat_count

        for _ in range(6):
            increment_chat_count("user-over")

        assert is_limit_exceeded("user-over") is True

    def test_new_user_is_not_exceeded(self):
        """チャット履歴のない新規ユーザーは制限超過と判定されない。"""
        from app.services.chat_count import is_limit_exceeded

        assert is_limit_exceeded("user-brand-new") is False


class TestScenario:
    def test_daily_chat_flow_reaches_limit(self):
        """ユーザーが5回チャットすると制限に達し、6回目は送れない流れ。"""
        from app.services.chat_count import (
            get_chat_count,
            increment_chat_count,
            is_limit_exceeded,
        )

        uid = "user-scenario"
        assert get_chat_count(uid) == 0
        assert is_limit_exceeded(uid) is False

        for i in range(1, 6):
            count = increment_chat_count(uid)
            assert count == i

        assert is_limit_exceeded(uid) is True

    def test_date_boundary_resets_count(self):
        """日付が変わると別の日のカウントが始まり、前日のカウントは参照されない。"""
        from app.services.chat_count import (
            get_chat_count,
            increment_chat_count,
        )

        uid = "user-boundary"

        with patch(
            "app.services.chat_count._today_jst", return_value="2024-01-01"
        ):
            for _ in range(5):
                increment_chat_count(uid)

        with patch(
            "app.services.chat_count._today_jst", return_value="2024-01-02"
        ):
            assert get_chat_count(uid) == 0
            increment_chat_count(uid)
            assert get_chat_count(uid) == 1
