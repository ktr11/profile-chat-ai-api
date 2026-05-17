import uuid
import pytest
from unittest.mock import patch

STUB_REPLY = "統合テスト用スタブ返答"


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("app.routers.chat.llm.invoke_chat", return_value=STUB_REPLY):
        yield


class TestFullFlowScenario:
    def test_新規ユーザーがセッション開始からチャット上限まで到達する(self, client):
        trial_uuid = str(uuid.uuid4())

        # セッション作成
        res = client.post("/session", cookies={"trial_uuid": trial_uuid})
        assert res.status_code == 200
        body = res.json()
        assert body["chat_count"] == 0
        assert body["chat_limit"] == 5

        # チャット5回送信 → すべて200
        for i in range(1, 6):
            res = client.post(
                "/chat",
                json={"message": f"メッセージ{i}"},
                cookies={"trial_uuid": trial_uuid},
            )
            assert res.status_code == 200, f"{i}回目が200以外: {res.status_code}"
            body = res.json()
            assert body["chat_count"] == i
            assert body["reply"] == STUB_REPLY

        # 6回目 → 403
        res = client.post(
            "/chat",
            json={"message": "上限超過メッセージ"},
            cookies={"trial_uuid": trial_uuid},
        )
        assert res.status_code == 403

    def test_複数ユーザーのカウントが独立している(self, client):
        uuid_a = str(uuid.uuid4())
        uuid_b = str(uuid.uuid4())

        # ユーザーAが3回チャット
        for _ in range(3):
            res = client.post(
                "/chat",
                json={"message": "hello"},
                cookies={"trial_uuid": uuid_a},
            )
            assert res.status_code == 200

        # ユーザーBは1回もチャットしていない → セッション確認でcount=0
        res = client.post("/session", cookies={"trial_uuid": uuid_b})
        assert res.status_code == 200
        assert res.json()["chat_count"] == 0

        # ユーザーAのカウントは3
        res = client.post("/session", cookies={"trial_uuid": uuid_a})
        assert res.status_code == 200
        assert res.json()["chat_count"] == 3

    def test_チャット履歴がllmに渡される(self, client):
        trial_uuid = str(uuid.uuid4())
        captured_histories = []

        def capture_invoke(history, user_message):
            captured_histories.append(list(history))
            return STUB_REPLY

        with patch("app.routers.chat.llm.invoke_chat", side_effect=capture_invoke):
            for msg in ["1回目", "2回目", "3回目"]:
                client.post(
                    "/chat",
                    json={"message": msg},
                    cookies={"trial_uuid": trial_uuid},
                )

        # 3回目の呼び出し時には直前の履歴が渡されている
        assert len(captured_histories) == 3
        # 2回目呼び出し時: 1往復分の履歴（user + assistant）
        assert len(captured_histories[1]) == 2
        # 3回目呼び出し時: 2往復分の履歴
        assert len(captured_histories[2]) == 4

    def test_cookieなしでは401が返る(self, client):
        res = client.post("/chat", json={"message": "hello"})
        assert res.status_code == 401
