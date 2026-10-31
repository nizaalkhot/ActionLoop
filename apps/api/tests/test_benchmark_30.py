import pytest
from routers.eval import run_golden_benchmark
from database import init_db

def test_run_model_benchmark():
    init_db()
    res = run_golden_benchmark(gemini_api_key="test-gemini-key", dataset="all")
    assert res["status"] == "completed"
    assert "gemini" in res["engine_used"].lower()
    assert "structured outputs" in res["engine_used"].lower()
    assert res["cases_evaluated"] == 40
    assert "breakdown" in res
