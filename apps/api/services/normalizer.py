import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple

class TranscriptNormalizer:
    @staticmethod
    def clean_and_parse(raw_text: str, default_date: str = None, default_tz: str = "UTC") -> Dict:
        """
        Parses raw meeting notes or transcripts.
        Cleans timestamp artifacts (SRT/VTT), normalizes speaker prefixes,
        and extracts speaker roster.
        """
        if not default_date:
            default_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Strip VTT header
        cleaned = re.sub(r"^WEBVTT.*?\n", "", raw_text, flags=re.IGNORECASE)
        # Strip timestamp lines like 00:01:23.000 --> 00:01:25.000
        cleaned = re.sub(r"\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?", "", cleaned)
        # Strip inline cue tags like <v Speaker> or <00:01:23>
        cleaned = re.sub(r"<\/?(?:v\s+[^>]+|[0-9:.]+)>", "", cleaned)
        
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

        detected_speakers = set()
        speaker_regex = re.compile(r"^(?:\[[\d:]+\]\s*)?([A-Za-z0-9\s._'-]+?)\s*:\s*(.*)$")

        normalized_segments = []
        for line in lines:
            match = speaker_regex.match(line)
            if match:
                speaker = match.group(1).strip()
                content = match.group(2).strip()
                # filter out non-speaker prefixes like "Note:", "Action:", "Date:"
                if speaker.lower() not in ["note", "notes", "action", "actions", "date", "todo", "agenda", "attendees"]:
                    detected_speakers.add(speaker)
                    normalized_segments.append(f"{speaker}: {content}")
                else:
                    normalized_segments.append(line)
            else:
                normalized_segments.append(line)

        clean_transcript = "\n".join(normalized_segments)

        return {
            "clean_transcript": clean_transcript,
            "detected_speakers": sorted(list(detected_speakers)),
            "anchor_date": default_date,
            "timezone": default_tz
        }

