from unittest.mock import patch

import pytest

STUB_REPLY = "テスト用スタブ返答"


@pytest.fixture(autouse=True)
def mock_llm():
    """llm.invoke_chatをモックして返答を固定する。"""
    with patch("app.routers.chat.llm.invoke_chat", return_value=STUB_REPLY):
        yield


def _start_session(client) -> str:
    """セッションを開始してtrial_uuidを返すヘルパー。"""
    res = client.post("/session")
    return res.cookies["trial_uuid"]


class TestPostChat:
    def test_正常なリクエストで200を返す(self, client):
        """cookieあり・制限未達のリクエストは200を返す。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        response = client.post("/chat", json={"message": "こんにちは"})

        assert response.status_code == 200

    def test_返答にreplyが含まれる(self, client):
        """レスポンスのreplyがllmの返答と一致する。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        response = client.post("/chat", json={"message": "テスト"})

        assert response.json()["reply"] == STUB_REPLY

    def test_chat_countが1増加する(self, client):
        """チャット送信後のchat_countが1になる。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        response = client.post("/chat", json={"message": "テスト"})

        assert response.json()["chat_count"] == 1

    def test_chat_limitが設定値と一致する(self, client):
        """レスポンスのchat_limitは設定のTRIAL_CHAT_LIMIT（デフォルト5）を返す。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        response = client.post("/chat", json={"message": "テスト"})

        assert response.json()["chat_limit"] == 5

    def test_cookieなしで401を返す(self, client):
        """trial_uuidクッキーがない場合は401を返す。"""
        response = client.post("/chat", json={"message": "こんにちは"})

        assert response.status_code == 401
        assert response.json()["detail"] == "セッションが開始されていません。"

    def test_上限超過で403を返す(self, client):
        """1日の上限（5回）を超えると403を返す。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        for _ in range(5):
            client.post("/chat", json={"message": "msg"})

        client.cookies.set("trial_uuid", uid)
        response = client.post("/chat", json={"message": "6回目"})

        assert response.status_code == 403
        assert response.json()["detail"] == "本日のチャット上限に達しました。"

    def test_messageフィールドなしで422を返す(self, client):
        """リクエストボディにmessageがない場合は422を返す。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)

        response = client.post("/chat", json={})

        assert response.status_code == 422

    def test_履歴がllmに渡される(self, client):
        """過去のメッセージがllm.invoke_chatのhistory引数に渡される。"""
        uid = _start_session(client)
        client.cookies.set("trial_uuid", uid)
        client.post("/chat", json={"message": "1回目"})

        with patch("app.routers.chat.llm.invoke_chat", return_value=STUB_REPLY) as mock:
            client.cookies.set("trial_uuid", uid)
            client.post("/chat", json={"message": "2回目"})
            history_passed = mock.call_args[0][0]

        # 1回目のuser/assistantメッセージが履歴に含まれる
        assert len(history_passed) == 2
        assert history_passed[0]["role"] == "user"
        assert history_passed[0]["content"] == "1回目"


class TestScenario:
    def test_5回チャットで上限到達フロー(self, client):
        """5回送信後に上限に達し、6回目は403になる一連フロー。"""
        uid = _start_session(client)

        for i in range(1, 6):
            client.cookies.set("trial_uuid", uid)
            res = client.post("/chat", json={"message": f"msg{i}"})
            assert res.status_code == 200
            assert res.json()["chat_count"] == i

        client.cookies.set("trial_uuid", uid)
        res = client.post("/chat", json={"message": "上限超過"})
        assert res.status_code == 403

    def test_チャット履歴が蓄積される(self, client):
        """複数回チャット後、llmに渡される履歴が空でなく蓄積されている。"""
        uid = _start_session(client)

        client.cookies.set("trial_uuid", uid)
        client.post("/chat", json={"message": "最初の質問"})

        with patch("app.routers.chat.llm.invoke_chat", return_value=STUB_REPLY) as mock:
            client.cookies.set("trial_uuid", uid)
            client.post("/chat", json={"message": "2回目の質問"})
            history_passed = mock.call_args[0][0]

        # 1往復分（user + assistant）= 2件が履歴として渡される
        assert len(history_passed) == 2
        assert history_passed[0]["role"] == "user"
        assert history_passed[0]["content"] == "最初の質問"
        assert history_passed[1]["role"] == "assistant"
        assert history_passed[1]["content"] == STUB_REPLY
