"""
Agent Orchestration Workflow for PitchSense.
Executes the full agent pipeline for each triggered match moment:
FactSheet -> HeadlineAgent -> GroundingValidator -> LensAgent -> ProducerAgent.
Handles retries and degraded-mode resilience on model failure.
"""

from typing import Dict, Any, Optional, List
from backend.agents.headline import HeadlineAgent
from backend.agents.validator import GroundingValidator
from backend.agents.lens import LensAgent
from backend.agents.producer import ProducerAgent

class AgentOrchestrator:
    def __init__(self):
        self.headline_agent = HeadlineAgent()
        self.validator = GroundingValidator()
        self.lens_agent = LensAgent()
        self.producer_agent = ProducerAgent()

    def process_moment(
        self,
        fact_sheet: Dict[str, Any],
        audience: str = "casual",
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Executes the agent pipeline for a detected moment.
        Returns the finalized PitchSenseBroadcastCue.
        """
        # 1. Headline Drafting
        draft, receipt = self.headline_agent.draft(fact_sheet)
        
        # 2. Grounding Validation Gate
        is_valid, refusal_reason = self.validator.validate(
            fact_sheet=fact_sheet,
            draft_headline=draft.get("headline", ""),
            draft_detail=draft.get("detail", ""),
            draft_evidence=draft.get("evidence", [])
        )
        
        if not is_valid:
            # Degraded-mode fallback: assemble verified facts directly without LLM embellishment
            receipt["validated"] = False
            receipt["refusal_reason"] = refusal_reason
            
            trigger = fact_sheet.get("trigger_type", "moment")
            team = fact_sheet.get("team", "")
            facts = fact_sheet.get("facts", [])
            fact_summary = ", ".join(f"{f['name']}: {f['value']} {f['unit']}" for f in facts[:2])
            
            draft = {
                "headline": f"Verified match telemetry: {team} {trigger.replace('_', ' ')}",
                "detail": fact_summary,
                "why": "Tactical change recorded directly from match engine telemetry.",
                "evidence": [f["fact_id"] for f in facts]
            }
        else:
            receipt["validated"] = True

        # 3. Personalization & Localization
        personalized_payload, lens_receipt = self.lens_agent.personalize(
            draft=draft,
            fact_sheet=fact_sheet,
            audience=audience,
            lang=lang
        )
        
        # Merge receipt metrics
        receipt["lens_latency_ms"] = lens_receipt.get("latency_ms", 0.0)

        # 4. Producer Cue Assembly
        cue = self.producer_agent.create_cue(
            fact_sheet=fact_sheet,
            payload=personalized_payload,
            receipt=receipt,
            audience=audience,
            lang=lang
        )

        return cue

    def get_refusal_log(self) -> List[Dict[str, Any]]:
        return self.validator.get_refusal_history()

    def get_all_cues(self) -> List[Dict[str, Any]]:
        return self.producer_agent.get_all_cues()
