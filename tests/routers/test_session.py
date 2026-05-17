class TestPostSession:
    def test_新規ユーザーにcookieが発行される(self, client):
        """cookie未設定のリクエストにtrial_uuidクッキーがセットされる。"""
        response = client.post("/session")

        assert response.status_code == 200
        assert "trial_uuid" in response.cookies

    def test_新規ユーザーのchat_countは0(self, client):
        """初回アクセス時のchat_countは0を返す。"""
        response = client.post("/session")

        body = response.json()
        assert body["chat_count"] == 0

    def test_chat_limitが設定値と一致する(self, client):
        """chat_limitは設定のTRIAL_CHAT_LIMIT（デフォルト5）を返す。"""
        response = client.post("/session")

        body = response.json()
        assert body["chat_limit"] == 5

    def test_既存cookieがあればchatカウントを返す(self, client):
        """既存のtrial_uuidクッキーがある場合はそのユーザーのカウントを返す。"""
        # 先にセッション開始してcookieを取得
        first = client.post("/session")
        uid = first.cookies["trial_uuid"]

        # チャットを1回送信してカウントを増やす
        with client:
            client.cookies.set("trial_uuid", uid)
            client.post("/chat", json={"message": "hello"})

        # 再度セッション取得
        client.cookies.set("trial_uuid", uid)
        second = client.post("/session")

        assert second.json()["chat_count"] == 1

    def test_既存cookieがあればcookieは再発行されない(self, client):
        """既存クッキーがある場合はSet-Cookieヘッダーが返らない。"""
        first = client.post("/session")
        uid = first.cookies["trial_uuid"]

        client.cookies.set("trial_uuid", uid)
        second = client.post("/session")

        assert "trial_uuid" not in second.headers.get("set-cookie", "")


class TestScenario:
    def test_セッション開始からチャット送信の基本フロー(self, client):
        """POST /session → POST /chat の一連フローでカウントが正しく増加する。"""
        session_res = client.post("/session")
        assert session_res.status_code == 200
        assert session_res.json()["chat_count"] == 0

        uid = session_res.cookies["trial_uuid"]
        client.cookies.set("trial_uuid", uid)

        chat_res = client.post("/chat", json={"message": "こんにちは"})
        assert chat_res.status_code == 200
        assert chat_res.json()["chat_count"] == 1

        client.cookies.set("trial_uuid", uid)
        session_res2 = client.post("/session")
        assert session_res2.json()["chat_count"] == 1
