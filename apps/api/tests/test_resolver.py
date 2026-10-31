import pytest
from services.resolver import EntityResolver

def test_resolve_owner():
    users = [
        {"id": "usr_priya", "name": "Priya Sharma", "email": "priya@startup.co"},
        {"id": "usr_alex", "name": "Alex Chen", "email": "alex@startup.co"},
        {"id": "usr_sarah", "name": "Sarah Jenkins", "email": "sarah@startup.co"}
    ]

    # Exact first name
    uid, uname, conf, is_ambiguous = EntityResolver.resolve_owner("Priya", users)
    assert uid == "usr_priya"
    assert uname == "Priya Sharma"
    assert conf >= 0.90
    assert is_ambiguous is False

    # Case insensitive
    uid, uname, conf, is_ambiguous = EntityResolver.resolve_owner("alex", users)
    assert uid == "usr_alex"
    assert uname == "Alex Chen"

    # Unknown person should return None and 0.0
    uid, uname, conf, is_ambiguous = EntityResolver.resolve_owner("RandomStranger", users)
    assert uid is None
    assert conf == 0.0

def test_resolve_due_date():
    # Anchor: Wednesday, 2026-11-04
    anchor = "2026-11-04"

    # Tomorrow -> Thursday 2026-11-05
    res, conf = EntityResolver.resolve_due_date("tomorrow", anchor)
    assert res == "2026-11-05"
    assert conf > 0.9

    # by Friday -> Friday 2026-11-06
    res, conf = EntityResolver.resolve_due_date("by Friday", anchor)
    assert res == "2026-11-06"
    assert conf > 0.9

    # by next Monday -> 2026-11-09
    res, conf = EntityResolver.resolve_due_date("by next Monday", anchor)
    assert res == "2026-11-09"

    # today
    res, conf = EntityResolver.resolve_due_date("today", anchor)
    assert res == "2026-11-04"

