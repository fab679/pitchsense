"""
Grounding Validator for PitchSense.
Pure deterministic code (no LLM). Recomputes numbers and checks cited facts.
Rejects ungrounded or hallucinated claims with structured refusal logs.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set

class GroundingValidator:
    def __init__(self):
        self.refusal_log: List[Dict[str, Any]] = []

    def _extract_numbers(self, text: str) -> List[float]:
        """Extracts numerical tokens from text, handling percentages, decimals, and metric units."""
        # Clean text
        clean = re.sub(r"(\d+):(\d+)", r"", text)  # ignore clock timestamps like 63:12
        # Match floats and integers
        matches = re.findall(r"\b\d+(?:\.\d+)?%?", clean)
        numbers = []
        for m in matches:
            if m.endswith("%"):
                try:
                    val = float(m[:-1])
                    numbers.append(val)
                    numbers.append(round(val / 100.0, 3)) # also allow fractional form
                except ValueError:
                    pass
            else:
                try:
                    numbers.append(float(m))
                except ValueError:
                    pass
        return numbers

    def _get_allowed_numbers(self, fact_sheet: Dict[str, Any]) -> Set[float]:
        """Collects all true numbers present in the FactSheet and context."""
        allowed = set()
        
        # Add minute
        minute = fact_sheet.get("minute", 0.0)
        allowed.add(round(float(minute), 0))
        allowed.add(round(float(minute), 1))
        
        # Add facts
        for f in fact_sheet.get("facts", []):
            val = f.get("value")
            if isinstance(val, (int, float)):
                f_val = float(val)
                allowed.add(f_val)
                allowed.add(round(f_val, 0))
                allowed.add(round(f_val, 1))
                allowed.add(round(f_val, 2))
                # Add percentage representation if between 0 and 1
                if 0.0 <= f_val <= 1.0:
                    allowed.add(round(f_val * 100.0, 0))
                    allowed.add(round(f_val * 100.0, 1))

        # Add context score
        ctx = fact_sheet.get("context", {})
        score = ctx.get("score", {})
        for s in score.values():
            allowed.add(float(s))

        # Common harmless numbers & scales: 1, 2, 3, 4, 5, 11 (players), 45, 90 (minutes), 100 (/100 scale), 105, 68 (pitch)
        allowed.update({0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 11.0, 45.0, 90.0, 100.0, 105.0, 68.0})
        return allowed

    def validate(
        self,
        fact_sheet: Dict[str, Any],
        draft_headline: str,
        draft_detail: str,
        draft_evidence: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates candidate commentary against the fact sheet.
        Returns: (is_valid, optional_refusal_reason).
        """
        valid_fact_ids = {f["fact_id"] for f in fact_sheet.get("facts", [])}
        
        # 1. Evidence Citation Verification
        if not draft_evidence:
            reason = "Refusal: Candidate text provided no grounded evidence citations."
            self._log_refusal(fact_sheet, draft_headline, draft_detail, draft_evidence, reason)
            return False, reason

        invalid_citations = [eid for eid in draft_evidence if eid not in valid_fact_ids and not eid.startswith("metric:")]
        if invalid_citations:
            reason = f"Refusal: Cited fact IDs {invalid_citations} not found in verified FactSheet."
            self._log_refusal(fact_sheet, draft_headline, draft_detail, draft_evidence, reason)
            return False, reason

        # 2. Number Verification
        allowed_nums = self._get_allowed_numbers(fact_sheet)
        text_nums = self._extract_numbers(f"{draft_headline} {draft_detail}")

        for num in text_nums:
            # Check if num is close to any allowed number (within tolerance of 0.5)
            is_grounded = any(abs(num - allowed) < 0.5 for allowed in allowed_nums)
            if not is_grounded:
                reason = f"Refusal: Ungrounded numerical claim detected ({num}). Number not present in verified match telemetry."
                self._log_refusal(fact_sheet, draft_headline, draft_detail, draft_evidence, reason)
                return False, reason

        return True, None

    def _log_refusal(self, fact_sheet: Dict[str, Any], headline: str, detail: str, evidence: List[str], reason: str):
        self.refusal_log.append({
            "moment_id": fact_sheet.get("moment_id"),
            "t_code": fact_sheet.get("t_code"),
            "headline": headline,
            "detail": detail,
            "evidence": evidence,
            "refusal_reason": reason
        })

    def get_refusal_history(self) -> List[Dict[str, Any]]:
        return list(self.refusal_log)

    def get_refusal_log(self) -> List[Dict[str, Any]]:
        return list(self.refusal_log)
