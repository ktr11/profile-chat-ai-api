import uuid
from unittest.mock import patch


class TestDateBoundary:
    def test_翌日になるとカウントがリセットされる(self, db):
        from app.services import chat_count

        trial_uuid = str(uuid.uuid4())

        # 今日の日付でカウントを積む
        with patch("app.services.chat_count._today_jst", return_value="2026-01-01"):
            for _ in range(3):
                chat_count.increment_chat_count(trial_uuid)
            count_today = chat_count.get_chat_count(trial_uuid)

        assert count_today == 3

        # 翌日になるとカウントは0にリセットされる
        with patch("app.services.chat_count._today_jst", return_value="2026-01-02"):
            count_tomorrow = chat_count.get_chat_count(trial_uuid)

        assert count_tomorrow == 0

    def test_翌日になると上限がリセットされる(self, db):
        from app.services import chat_count

        trial_uuid = str(uuid.uuid4())

        # 今日の日付で上限到達
        with patch("app.services.chat_count._today_jst", return_value="2026-01-01"):
            for _ in range(5):
                chat_count.increment_chat_count(trial_uuid)
            assert chat_count.is_limit_exceeded(trial_uuid) is True

        # 翌日になると上限リセット
        with patch("app.services.chat_count._today_jst", return_value="2026-01-02"):
            assert chat_count.is_limit_exceeded(trial_uuid) is False

    def test_翌日にチャットしたカウントは独立して積まれる(self, db):
        from app.services import chat_count

        trial_uuid = str(uuid.uuid4())

        # 今日2回
        with patch("app.services.chat_count._today_jst", return_value="2026-01-01"):
            chat_count.increment_chat_count(trial_uuid)
            chat_count.increment_chat_count(trial_uuid)

        # 翌日1回
        with patch("app.services.chat_count._today_jst", return_value="2026-01-02"):
            chat_count.increment_chat_count(trial_uuid)
            count = chat_count.get_chat_count(trial_uuid)

        assert count == 1

    def test_異なるユーザーの日付境界は独立している(self, db):
        from app.services import chat_count

        uuid_a = str(uuid.uuid4())
        uuid_b = str(uuid.uuid4())

        with patch("app.services.chat_count._today_jst", return_value="2026-01-01"):
            for _ in range(5):
                chat_count.increment_chat_count(uuid_a)
            chat_count.increment_chat_count(uuid_b)

        # 翌日: Aはリセット、Bもリセット
        with patch("app.services.chat_count._today_jst", return_value="2026-01-02"):
            assert chat_count.get_chat_count(uuid_a) == 0
            assert chat_count.get_chat_count(uuid_b) == 0
