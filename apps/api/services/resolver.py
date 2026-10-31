import re
from datetime import datetime, timedelta
import dateutil.parser
from typing import Dict, List, Optional, Tuple

class EntityResolver:
    @staticmethod
    def resolve_owner(
        raw_owner: Optional[str],
        workspace_users: List[Dict],
        speaker_context: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], float, bool]:
        """
        Resolves spoken owner ("Priya", "Alex", "I will", "myself") to a workspace user ID and full name.
        Returns: (user_id, user_name, confidence, is_ambiguous)
        """
        if not raw_owner:
            return None, None, 0.0, False

        target = raw_owner.strip().lower()

        # Handle first-person pronoun references if speaker context is known
        if target in ["i", "me", "myself", "i'll", "i will"] and speaker_context:
            target = speaker_context.strip().lower()

        # Check for multiple first name matches (e.g. Alex Chen vs Alex Miller)
        matching_users = []
        for user in workspace_users:
            full_name = user.get("name", "").lower()
            first_name = full_name.split()[0] if full_name else ""

            # Exact full name match
            if target == full_name:
                return user.get("id"), user.get("name"), 1.0, False

            # Exact first name match
            if target == first_name:
                matching_users.append((user, 0.95))
            elif target in full_name or full_name in target:
                matching_users.append((user, 0.85))
            elif len(target) >= 3 and (target in user.get("email", "").lower() or first_name.startswith(target)):
                matching_users.append((user, 0.75))

        # Disambiguate if more than one user matched with high score
        first_name_candidates = [u for u, score in matching_users if score >= 0.85]
        if len(first_name_candidates) > 1:
            # Check if speaker context matches exactly one
            if speaker_context:
                spk_lower = speaker_context.lower()
                disambiguated = [u for u in first_name_candidates if spk_lower in u.get("name", "").lower()]
                if len(disambiguated) == 1:
                    return disambiguated[0].get("id"), disambiguated[0].get("name"), 0.90, False

            # Ambiguous: do NOT guess arbitrarily! Leave unassigned so human confirms.
            return None, None, 0.40, True

        if matching_users:
            best_user, best_score = max(matching_users, key=lambda x: x[1])
            if best_score >= 0.70:
                return best_user.get("id"), best_user.get("name"), best_score, False

        return None, None, 0.0, False

    @staticmethod
    def resolve_due_date(raw_date_str: Optional[str], anchor_date_str: str, timezone_str: str = "UTC") -> Tuple[Optional[str], float]:
        """
        Converts relative natural language dates ('by Friday', 'tomorrow', 'next Monday', 'in 3 days')
        into an absolute ISO date (YYYY-MM-DD) based on anchor_date_str and local timezone.
        Returns: (resolved_iso_date, confidence)
        """
        if not raw_date_str or not raw_date_str.strip():
            return None, 0.0

        text = raw_date_str.strip().lower()

        # Handle ISO strings or dates with timezone
        try:
            if "t" in anchor_date_str.lower():
                parsed_anchor = dateutil.parser.parse(anchor_date_str)
                anchor_dt = datetime(parsed_anchor.year, parsed_anchor.month, parsed_anchor.day)
            else:
                anchor_dt = datetime.strptime(anchor_date_str.split()[0], "%Y-%m-%d")
        except Exception:
            anchor_dt = datetime.now()

        # Clean noise prefixes
        text = re.sub(r"^(by|before|until|on|due|for|around)\s+", "", text).strip()

        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        # Check 'today', 'tonight', 'eod'
        if text in ["today", "tonight", "end of day", "eod"]:
            return anchor_dt.strftime("%Y-%m-%d"), 0.98

        # Check 'tomorrow'
        if text.startswith("tomorrow"):
            target_dt = anchor_dt + timedelta(days=1)
            return target_dt.strftime("%Y-%m-%d"), 0.98

        # Check 'in X days'
        in_days_match = re.search(r"in\s+(\d+|one|two|three|four|five)\s+days?", text)
        if in_days_match:
            val_str = in_days_match.group(1).lower()
            word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            days = word_map.get(val_str) or int(val_str)
            return (anchor_dt + timedelta(days=days)).strftime("%Y-%m-%d"), 0.95

        # Check 'in X weeks' (e.g. in 2 weeks, in two weeks)
        in_weeks_match = re.search(r"in\s+(\d+|one|two|three|four)\s+weeks?", text)
        if in_weeks_match:
            val_str = in_weeks_match.group(1).lower()
            word_map = {"one": 1, "two": 2, "three": 3, "four": 4}
            weeks = word_map.get(val_str) or int(val_str)
            return (anchor_dt + timedelta(weeks=weeks)).strftime("%Y-%m-%d"), 0.95

        # Check 'end of next week'
        if "end of next week" in text:
            days_to_friday = (4 - anchor_dt.weekday()) % 7
            if days_to_friday == 0:
                days_to_friday = 7
            return (anchor_dt + timedelta(days=days_to_friday + 7)).strftime("%Y-%m-%d"), 0.90

        # Check 'next week'
        if "next week" in text:
            days_ahead = (0 - anchor_dt.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (anchor_dt + timedelta(days=days_ahead)).strftime("%Y-%m-%d"), 0.85

        # Check weekday names like "friday", "this friday", "next friday", "this coming friday"
        for day_name, day_idx in weekday_map.items():
            if day_name in text:
                current_weekday = anchor_dt.weekday()
                days_ahead = (day_idx - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target_dt = anchor_dt + timedelta(days=days_ahead)
                return target_dt.strftime("%Y-%m-%d"), 0.92

        # Check 'end of week' / 'eow'
        if "end of week" in text or "eow" in text:
            days_to_friday = (4 - anchor_dt.weekday()) % 7
            if days_to_friday == 0:
                days_to_friday = 7
            return (anchor_dt + timedelta(days=days_to_friday)).strftime("%Y-%m-%d"), 0.90

        # Attempt standard dateutil parse with anchor fallback
        try:
            parsed = dateutil.parser.parse(text, fuzzy=True, default=anchor_dt)
            if parsed < anchor_dt - timedelta(days=1):
                parsed = parsed.replace(year=anchor_dt.year + 1)
            return parsed.strftime("%Y-%m-%d"), 0.80
        except Exception:
            return None, 0.0
