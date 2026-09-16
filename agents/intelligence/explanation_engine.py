import json
import logging
import os
from typing import Dict, Any, List
from uuid import UUID

from jinja2 import Environment, FileSystemLoader

from backend.db.models.analytics import RiskScore, Explanation, Alert, Prediction
from backend.db.models.entities import Relationship
from sqlalchemy.orm import Session
from agents.extraction.providers import LLMProvider, MockDeterministicProvider

logger = logging.getLogger(__name__)

FORBIDDEN_TERMS = [
    "guilt ratio",
    "crime probability",
    "probability of guilt",
    "guilt score",
    "criminal probability",
    "probability that",
    "likely guilty",
    "is guilty",
]

class ExplanationEngine:
    """
    Generates structured, safe explanations for priority rankings using an AI provider
    or deterministic Jinja2 fallback.
    """
    
    def __init__(self, db: Session, provider: LLMProvider):
        self.db = db
        self.provider = provider
        
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _has_forbidden_terms(self, text: str) -> bool:
        lower_text = text.lower()
        for term in FORBIDDEN_TERMS:
            if term in lower_text:
                return True
        return False

    def generate_explanation(self, risk_score: RiskScore, case_id: UUID) -> Explanation:
        """
        Generates and returns an Explanation object.
        Does not commit to DB.
        """
        context = self._build_context(risk_score, case_id)
        
        prompt = f"Please explain the priority ranking based on this data: {json.dumps(context, default=str)}"
        system_prompt = (
            "You are an investigative assistant generating an explanation for a Priority Ranking. "
            "You MUST output a JSON object with these exact keys: "
            "summary, top_contributors, evidence_context, model_context, confidence_semantics, limitations, human_review_note. "
            "CRITICAL RULES: NEVER use the words 'guilt', 'probability of crime', or claim the entity committed an offense. "
            "This is an investigative lead, not a determination of guilt. "
            "Never invent facts not present in the data."
        )

        explanation_text = ""
        provider_type = "LLM"
        
        try:
            # Generate from AI
            ai_response = "sync" # Need async? This is called from a sync context usually.
            # Actually, `provider.generate_extraction` is `async`.
            # To avoid async loops in this context, we will run it via an event loop if needed, 
            # or if we are inside an async endpoint, we need `async def`.
            # We'll make this method async.
            pass
        except Exception:
            pass
            
        # Refactoring to async method below
        raise NotImplementedError("Use async_generate_explanation instead.")

    async def async_generate_explanation(self, risk_score: RiskScore, case_id: UUID) -> Explanation:
        """
        Generates and returns an Explanation object.
        Does not commit to DB.
        """
        context = self._build_context(risk_score, case_id)
        
        prompt = f"Please explain the priority ranking based on this data: {json.dumps(context, default=str)}"
        system_prompt = (
            "You are an investigative assistant generating an explanation for a Priority Ranking. "
            "You MUST output a JSON object with these exact keys: "
            "summary, top_contributors, evidence_context, model_context, confidence_semantics, limitations, human_review_note. "
            "CRITICAL RULES: NEVER use the words 'guilt', 'probability of crime', or claim the entity committed an offense. "
            "This is an investigative lead, not a determination of guilt. "
            "Never invent facts not present in the data."
        )

        explanation_text = ""
        provider_type = "LLM"
        is_valid = False
        
        try:
            ai_response = await self.provider.generate_extraction(prompt, system_prompt)
            if self._has_forbidden_terms(ai_response):
                logger.warning(f"Forbidden terminology detected in LLM response for Score {risk_score.score_id}. Falling back.")
            else:
                try:
                    # Validate JSON structure
                    parsed = json.loads(ai_response)
                    required_keys = ["summary", "top_contributors", "evidence_context", "model_context", "confidence_semantics", "limitations", "human_review_note"]
                    if all(k in parsed for k in required_keys):
                        explanation_text = ai_response
                        is_valid = True
                except json.JSONDecodeError:
                    logger.warning(f"LLM returned invalid JSON for Score {risk_score.score_id}. Falling back.")
        except Exception as e:
            logger.warning(f"LLM Provider failed for Score {risk_score.score_id}: {e}. Falling back.")

        if not is_valid:
            # Fallback to deterministic Jinja2 template
            template = self.jinja_env.get_template("explanation_fallback.j2")
            explanation_text = template.render(**context)
            provider_type = "TEMPLATE"

        return Explanation(
            score_id=risk_score.score_id,
            target_entity_uuid=risk_score.target_entity_uuid,
            case_id=case_id,
            run_id=risk_score.run_id,
            explanation_text=explanation_text,
            summary="Investigative Lead Context",
            context_data=context,
            model_version="1.0",
            provider_type=provider_type
        )

    def _build_context(self, risk_score: RiskScore, case_id: UUID) -> Dict[str, Any]:
        """
        Builds the context object used for Jinja2 rendering or LLM prompt.
        """
        components = risk_score.features_summary.get("components", {})
        contributions = risk_score.features_summary.get("contributions", {})
        
        # Sort contributors
        sorted_feats = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        top_features = [{"name": k, "value": v} for k, v in sorted_feats if v > 0]

        # Gather some basic evidence counts for the entity
        active_alerts_count = self.db.query(Alert).filter(
            Alert.case_id == case_id
        ).count() # Just an approximation for the case/entity
        
        observed_rels_count = self.db.query(Relationship).filter(
            Relationship.case_id == case_id,
            Relationship.status == "OBSERVED"
        ).count()

        return {
            "risk_score": {
                "value": risk_score.value,
                "score_id": str(risk_score.score_id)
            },
            "top_features": top_features,
            "active_alerts_count": active_alerts_count,
            "observed_rels_count": observed_rels_count,
            "model_run_id": str(risk_score.run_id),
            "template_version": "1.0",
            "entity_id": str(risk_score.target_entity_uuid)
        }
