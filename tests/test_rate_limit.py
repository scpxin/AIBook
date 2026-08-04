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


def test_x_forwarded_for_rate_limit_key():
    """限流键应读取 X-Forwarded-For 首个 IP（兼容 nginx 反代）"""
    from unittest.mock import Mock
    
    req1 = Mock()
    req1.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
    req1.client = Mock(host="10.0.0.1")
    
    req2 = Mock()
    req2.headers = {}
    req2.client = Mock(host="10.0.0.2")
    
    assert main._client_ip(req1) == "1.2.3.4"
    assert main._client_ip(req2) == "10.0.0.2"


def test_xff_multiple_ips():
    """XFF含多个 IP 时取第一个"""
    from unittest.mock import Mock
    
    req = Mock()
    req.headers = {"x-forwarded-for": "8.8.8.8,1.1.1.1,cloudflare"}
    req.client = Mock(host="127.0.0.1")
    
    assert main._client_ip(req) == "8.8.8.8"
