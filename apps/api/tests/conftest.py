import pytest
from unittest.mock import patch, MagicMock
import json
from config import settings

@pytest.fixture(autouse=True)
def mock_gemini_api():
    """
    Mocks the Gemini API HTTP response during unit tests when no live GEMINI_API_KEY is present,
    returning high-fidelity structured JSON outputs matching the prompt context.
    """
    if not settings.gemini_api_key:
        settings.gemini_api_key = "test-mock-gemini-api-key"

    with patch("requests.post") as mock_post:
        def side_effect(url, *args, **kwargs):
            if "generativelanguage.googleapis.com" in url:
                payload = kwargs.get("json", {})
                contents = payload.get("contents", [{}])[0].get("parts", [{}])[0].get("text", "")

                tasks = []
                if "auth" in contents.lower():
                    tasks.append({
                        "title": "Refactor authentication middleware",
                        "description": "Refactor auth middleware to support refresh tokens",
                        "raw_owner": "Alex",
                        "raw_due_date": "by Friday",
                        "supporting_quote": "Alex: I'll refactor the authentication middleware by Friday.",
                        "task_type": "feature",
                        "confidence": 0.95
                    })
                if "navigation" in contents.lower() or "drawer" in contents.lower():
                    tasks.append({
                        "title": "Fix mobile navigation drawer overlap on iOS",
                        "description": "Fix navigation drawer overlap bug",
                        "raw_owner": "Priya",
                        "raw_due_date": "by tomorrow",
                        "supporting_quote": "Priya: I will fix the mobile navigation drawer by tomorrow.",
                        "task_type": "bug",
                        "confidence": 0.92
                    })
                if "checkout" in contents.lower():
                    tasks.append({
                        "title": "Update checkout component",
                        "description": "Update checkout component today",
                        "raw_owner": "Priya",
                        "raw_due_date": "today",
                        "supporting_quote": "Priya: I will update the checkout component today.",
                        "task_type": "feature",
                        "confidence": 0.94
                    })
                if "redis" in contents.lower():
                    tasks.append({
                        "title": "Upgrade Redis cluster",
                        "description": "Upgrade the Redis cluster by Friday",
                        "raw_owner": "Sarah",
                        "raw_due_date": "by Friday",
                        "supporting_quote": "Sarah: I will upgrade the Redis cluster by Friday.",
                        "task_type": "chore",
                        "confidence": 0.91
                    })
                if "secret" in contents.lower():
                    tasks.append({
                        "title": "Finish secret prototype",
                        "description": "Secret project prototype",
                        "raw_owner": "Alex Chen",
                        "raw_due_date": "by Friday",
                        "supporting_quote": "Alex Chen: I will finish the secret prototype by Friday.",
                        "task_type": "feature",
                        "confidence": 0.90
                    })

                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": json.dumps({"tasks": tasks})}
                                ]
                            }
                        }
                    ]
                }
                mock_resp.raise_for_status = MagicMock()
                return mock_resp

            # Default return for any other requests
            default_resp = MagicMock()
            default_resp.status_code = 200
            default_resp.json.return_value = {}
            default_resp.raise_for_status = MagicMock()
            return default_resp

        mock_post.side_effect = side_effect
        yield mock_post
