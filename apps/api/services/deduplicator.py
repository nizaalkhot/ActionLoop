import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

class TaskDeduplicator:
    CONTRASTING_NOUNS = [
        ({"page", "frontend", "ui", "view", "screen"}, {"doc", "document", "spec", "notion", "wiki", "readme"}),
        ({"ios", "iphone", "ipad", "apple"}, {"android", "pixel"}),
        ({"staging", "dev", "test"}, {"prod", "production"}),
        ({"auth", "login"}, {"billing", "checkout", "payment"}),
    ]

    @staticmethod
    def _normalize_token(w: str) -> str:
        w = w.lower()
        if w.startswith("auth"):
            return "auth"
        if w.endswith("ies") and len(w) > 4:
            return w[:-3] + "y"
        if w.endswith("ing") and len(w) > 4:
            return w[:-3]
        if w.endswith("ed") and len(w) > 3:
            return w[:-2]
        if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
            return w[:-1]
        return w

    @classmethod
    def _tokenize(cls, text: str) -> set:
        raw_tokens = re.findall(r"\w+", text.lower())
        stopwords = {"the", "a", "an", "is", "for", "to", "on", "in", "and", "or", "we", "i", "need", "should", "will", "please", "by", "with", "of", "and"}
        return {cls._normalize_token(t) for t in raw_tokens if t not in stopwords and len(t) >= 3}

    @classmethod
    def _has_contrasting_nouns(cls, tokens_a: set, tokens_b: set) -> bool:
        """
        Detects if two titles differ on mutually exclusive critical nouns (e.g. 'page' vs 'doc', 'ios' vs 'android').
        """
        for group_a, group_b in cls.CONTRASTING_NOUNS:
            if (tokens_a & group_a and tokens_b & group_b) or (tokens_a & group_b and tokens_b & group_a):
                return True
        return False

    @classmethod
    def check_duplicate(
        cls,
        candidate_title: str,
        existing_tickets: List[Dict],
        threshold: float = 0.60
    ) -> Tuple[Optional[str], float]:
        """
        Calculates semantic similarity between candidate task title and active tickets.
        Applies noun contrast penalties to avoid false positives (e.g. 'pricing page' vs 'pricing doc').
        Returns: (matched_ticket_summary, similarity_score)
        """
        if not candidate_title or not existing_tickets:
            return None, 0.0

        cand_tokens = cls._tokenize(candidate_title)
        best_match = None
        best_score = 0.0

        for ticket in existing_tickets:
            ticket_title = ticket.get("title", "")
            ticket_id = ticket.get("id", "")
            ticket_tokens = cls._tokenize(ticket_title)

            # Check for conflicting entities (e.g. page vs doc)
            if cls._has_contrasting_nouns(cand_tokens, ticket_tokens):
                # Strong penalty: distinct objects
                contrast_penalty = 0.35
            else:
                contrast_penalty = 0.0

            # 1. Sequence matcher
            seq_score = SequenceMatcher(None, candidate_title.lower(), ticket_title.lower()).ratio()

            # 2. Token Jaccard & Containment with normalized stems
            if cand_tokens and ticket_tokens:
                intersection = len(cand_tokens & ticket_tokens)
                union = len(cand_tokens | ticket_tokens)
                jaccard = intersection / union if union > 0 else 0.0
                containment = intersection / len(cand_tokens) if cand_tokens else 0.0
                token_score = max(jaccard, containment * 0.85)
            else:
                token_score = 0.0

            # 3. Bi-gram character similarity for handling paraphrases
            def get_bigrams(s):
                clean = re.sub(r"\s+", "", s.lower())
                return {clean[i:i+2] for i in range(len(clean)-1)}

            bg_cand = get_bigrams(candidate_title)
            bg_ticket = get_bigrams(ticket_title)
            bg_score = (2.0 * len(bg_cand & bg_ticket)) / (len(bg_cand) + len(bg_ticket)) if (bg_cand and bg_ticket) else 0.0

            # Combined weighted score
            combined = (0.30 * seq_score + 0.40 * token_score + 0.30 * bg_score) - contrast_penalty
            combined = max(0.0, min(1.0, combined))

            if combined > best_score:
                best_score = combined
                best_match = f"{ticket_id}: {ticket_title}"

        if best_score >= threshold:
            return best_match, round(best_score, 2)

        return None, round(best_score, 2)
