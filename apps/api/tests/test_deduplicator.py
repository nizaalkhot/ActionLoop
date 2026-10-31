import pytest
from services.deduplicator import TaskDeduplicator

def test_deduplicator():
    existing = [
        {"id": "LIN-101", "title": "Refactor authentication middleware for JWT refresh tokens"},
        {"id": "LIN-102", "title": "Fix mobile navigation drawer overlap on iOS Safari"}
    ]

    # Similar task should flag duplicate
    matched, score = TaskDeduplicator.check_duplicate("Refactor auth middleware to handle refresh token rotation", existing)
    assert matched is not None
    assert "LIN-101" in matched
    assert score >= 0.55

    # Completely different task should not flag
    matched, score = TaskDeduplicator.check_duplicate("Configure Stripe webhook endpoint", existing)
    assert matched is None
    assert score < 0.55

