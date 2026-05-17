from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def setup(aws_mock):
    pass


class TestSaveMessage:
    def test_saves_user_message(self):
        """ユーザーロールのメッセージが正しく保存・取得できる。"""
        from app.services.chat_history import save_message, get_recent_history

        save_message("user-a", "user", "こんにちは")
        history = get_recent_history("user-a")

        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "こんにちは"

    def test_saves_assistant_message(self):
        """アシスタントロールのメッセージが正しく保存・取得できる。"""
        from app.services.chat_history import save_message, get_recent_history

        save_message("user-b", "assistant", "はい、承知しました。")
        history = get_recent_history("user-b")

        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == "はい、承知しました。"

    def test_multiple_messages_are_stored(self):
        """複数のメッセージをすべて保存できる。"""
        from app.services.chat_history import save_message, get_recent_history

        # time.time()をモックしてタイムスタンプの衝突を防ぐ
        for i, (role, msg) in enumerate([("user", "質問1"), ("assistant", "回答1"), ("user", "質問2")]):
            with patch("app.services.chat_history.time") as mock_time:
                mock_time.time.return_value = i + 1
                save_message("user-c", role, msg)

        history = get_recent_history("user-c")
        assert len(history) == 3


class TestGetRecentHistory:
    def test_returns_empty_for_new_user(self):
        """履歴のない新規ユーザーは空リストを返す。"""
        from app.services.chat_history import get_recent_history

        assert get_recent_history("user-new") == []

    def test_returns_in_chronological_order(self):
        """メッセージはタイムスタンプの昇順（古い順）で返される。"""
        from app.services.chat_history import save_message, get_recent_history

        uid = "user-order"
        timestamps = [1000, 2000, 3000]
        messages = ["最初", "次", "最後"]

        for ts, msg in zip(timestamps, messages):
            with patch("app.services.chat_history.time") as mock_time:
                mock_time.time.return_value = ts / 1000
                save_message(uid, "user", msg)

        history = get_recent_history(uid)
        contents = [h["content"] for h in history]
        assert contents == ["最初", "次", "最後"]

    def test_respects_chat_history_limit(self):
        """取得件数が設定値（CHAT_HISTORY_LIMIT=10）を超えない。"""
        from app.services.chat_history import save_message, get_recent_history

        uid = "user-limit"
        for i in range(15):
            with patch("app.services.chat_history.time") as mock_time:
                mock_time.time.return_value = i
                save_message(uid, "user", f"msg{i}")

        history = get_recent_history(uid)
        assert len(history) <= 10

    def test_different_users_are_isolated(self):
        """異なるユーザーの履歴は互いに独立している。"""
        from app.services.chat_history import save_message, get_recent_history

        save_message("user-x", "user", "ユーザーXのメッセージ")
        save_message("user-y", "user", "ユーザーYのメッセージ")

        history_x = get_recent_history("user-x")
        history_y = get_recent_history("user-y")

        assert len(history_x) == 1
        assert history_x[0]["content"] == "ユーザーXのメッセージ"
        assert len(history_y) == 1
        assert history_y[0]["content"] == "ユーザーYのメッセージ"


class TestScenario:
    def test_conversation_turn_flow(self):
        """ユーザーとアシスタントが交互に会話するフロー。"""
        from app.services.chat_history import save_message, get_recent_history

        uid = "user-conversation"
        turns = [
            ("user", "FastAPIについて教えて"),
            ("assistant", "FastAPIはPythonのWebフレームワークです。"),
            ("user", "使い方は？"),
            ("assistant", "uvicornで起動します。"),
        ]

        ts = 1000
        for role, msg in turns:
            with patch("app.services.chat_history.time") as mock_time:
                mock_time.time.return_value = ts / 1000
                save_message(uid, role, msg)
            ts += 1000

        history = get_recent_history(uid)
        assert len(history) == 4
        for i, (role, msg) in enumerate(turns):
            assert history[i]["role"] == role
            assert history[i]["content"] == msg

    def test_history_limit_returns_most_recent(self):
        """履歴制限に達した場合、最新のメッセージが返される（古いものが切られる）。"""
        from app.services.chat_history import save_message, get_recent_history

        uid = "user-overflow"
        for i in range(12):
            with patch("app.services.chat_history.time") as mock_time:
                mock_time.time.return_value = i
                save_message(uid, "user", f"message-{i}")

        history = get_recent_history(uid)
        assert len(history) == 10
        # 最新10件（index 2〜11）が返されるはず
        contents = [h["content"] for h in history]
        assert "message-2" in contents
        assert "message-11" in contents
        assert "message-0" not in contents
        assert "message-1" not in contents
