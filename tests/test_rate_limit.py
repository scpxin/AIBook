"""限流中间件测试"""
import time

from app import main


def _fill_store(app, client_ip, count):
    now = time.time()
    main._rate_limit_store.clear()
    main._rate_limit_store[client_ip] = [now] * count


def test_write_methods_rate_limited(app, client):
    _fill_store(app, "testclient", main.RATE_LIMIT_MAX)
    resp = client.post("/api/v2/projects", json={"name": "x"})
    assert resp.status_code == 429


def test_mutating_get_rate_limited(app, client):
    _fill_store(app, "testclient", main.RATE_LIMIT_MAX)
    resp = client.get("/api/download/start", params={"book_id": "123"})
    assert resp.status_code == 429


def test_plain_get_not_rate_limited(app, client):
    _fill_store(app, "testclient", main.RATE_LIMIT_MAX)
    resp = client.get("/api/health")
    assert resp.status_code != 429
