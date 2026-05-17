class TestHealth:
    def test_ステータスokを返す(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
