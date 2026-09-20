import pytest
from pipeline.llm_client import LLMClient, LLMError


def test_complete_returns_text_via_injected_post():
    def fake_post(url, headers, json, timeout):
        class R:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "hello"}}]}
            def raise_for_status(self):
                pass
        assert timeout == 30  # timeout 必须被传入
        return R()

    client = LLMClient(api_key="k", base_url="http://x/v1", model="m",
                       timeout=30, http_post=fake_post)
    assert client.complete("sys", "usr") == "hello"


def test_complete_raises_llmerror_on_network_failure():
    def boom(url, headers, json, timeout):
        raise ConnectionError("down")

    client = LLMClient(api_key="k", base_url="http://x/v1", model="m",
                       timeout=30, http_post=boom)
    with pytest.raises(LLMError):
        client.complete("sys", "usr")


def test_from_env_reads_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "envkey")
    monkeypatch.setenv("LLM_BASE_URL", "http://y/v1")
    monkeypatch.setenv("LLM_MODEL_ID", "mm")
    client = LLMClient.from_env()
    assert client.api_key == "envkey"
    assert client.model == "mm"
