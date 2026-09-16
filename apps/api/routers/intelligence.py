from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CopilotQueryRequest(BaseModel):
    query: str
    context_filters: Optional[Dict[str, Any]] = None

class CopilotQueryResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]] = []

from backend.db.session import get_db
from backend.db.models.analytics import RiskScore, Explanation
from backend.db.models.entities import Entity
from backend.security.rbac import Permissions
from apps.api.deps import CaseAuthContext, verify_case_access

from agents.intelligence.priority_engine import PriorityEngine
from agents.intelligence.explanation_engine import ExplanationEngine
from agents.extraction.providers import GenericHTTPProvider
import os

router = APIRouter(prefix="/cases/{case_id}/intelligence", tags=["Intelligence"])

# A default LLM provider for the explanation engine
def get_llm_provider() -> GenericHTTPProvider:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    return GenericHTTPProvider(
        endpoint_url="https://api.openai.com/v1/chat/completions",
        api_key=api_key,
        model_name="gpt-4o-mini"
    )

@router.post("/priority-rankings", status_code=status.HTTP_201_CREATED)
def generate_priority_rankings(
    case_id: UUID,
    db: Session = Depends(get_db),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_UPDATE))
):
    # 1. Run priority engine
    priority_engine = PriorityEngine(db, case_id)
    risk_scores = priority_engine.run_priority_ranking()
    db.commit()

    return {"message": f"Generated priority rankings for {len(risk_scores)} entities.", "run_id": str(risk_scores[0].run_id) if risk_scores else None}

@router.get("/leads")
def get_investigative_leads(
    case_id: UUID,
    db: Session = Depends(get_db),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ))
):
    # Get latest risk scores for this case
    # In a real app we might fetch by latest run_id or group by entity and take latest.
    # For now, let's just get the top 50 risk scores for this case.
    # RiskScore doesn't have case_id directly, but we can join with Entity.
    scores = db.query(RiskScore).join(Entity).filter(
        Entity.case_id == case_id,
        RiskScore.score_type == "PRIORITY_RANKING"
    ).order_by(RiskScore.value.desc()).limit(50).all()

    results = []
    for score in scores:
        results.append({
            "entity_id": str(score.target_entity_uuid),
            "canonical_name": score.entity.canonical_name,
            "priority_score": score.value,
            "rank": len(results) + 1,
            "score_id": str(score.score_id),
            "run_id": str(score.run_id)
        })

    return {"investigative_leads": results}

@router.get("/leads/{entity_id}/explanation")
async def get_lead_explanation(
    case_id: UUID,
    entity_id: UUID,
    db: Session = Depends(get_db),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ))
):
    # Ensure entity exists in this case
    entity = db.query(Entity).filter(Entity.entity_id == entity_id, Entity.case_id == case_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found in this case.")

    # Get latest score
    score = db.query(RiskScore).filter(
        RiskScore.target_entity_uuid == entity_id,
        RiskScore.score_type == "PRIORITY_RANKING"
    ).order_by(RiskScore.score_id.desc()).first() # In real app, order by run date

    if not score:
        raise HTTPException(status_code=404, detail="No priority ranking found for this entity.")

    # Check if explanation already exists
    explanation = db.query(Explanation).filter(Explanation.score_id == score.score_id).first()
    
    if not explanation:
        # Generate on the fly
        provider = get_llm_provider()
        engine = ExplanationEngine(db, provider)
        explanation = await engine.async_generate_explanation(score, case_id)
        db.add(explanation)
        db.commit()

    # If it's a JSON string from LLM, parse it. Otherwise, wrap Jinja2 output.
    try:
        import json
        if explanation.provider_type == "LLM":
            content = json.loads(explanation.explanation_text)
        else:
            content = {"summary": explanation.explanation_text}
    except Exception:
        content = {"summary": explanation.explanation_text}

    return {
        "explanation_id": str(explanation.explanation_id),
        "score_id": str(explanation.score_id),
        "target_entity_uuid": str(explanation.target_entity_uuid),
        "provider_type": explanation.provider_type,
        "content": content,
        "model_version": explanation.model_version
    }

@router.post("/copilot/query", response_model=CopilotQueryResponse)
async def query_copilot(
    case_id: UUID,
    request: CopilotQueryRequest,
    db: Session = Depends(get_db),
    auth_ctx: CaseAuthContext = Depends(verify_case_access(Permissions.CASE_READ))
):
    provider = get_llm_provider()
    
    # Base system instructions - strictly instructing no markdown
    sys_prompt = (
        "You are an expert criminal network analysis AI copilot for the CNAS Intelligence Workstation.\n"
        "Your role is to formulate detailed, understandable answers to investigative queries.\n"
        "CRITICAL FORMATTING RULES:\n"
        "- DO NOT use any markdown formatting like stars (*), hashes (#), or underscores (_).\n"
        "- Provide raw text answers only.\n"
        "- Format with clean line breaks and plain text bullet points (e.g. using dashes or numbers) if needed.\n"
    )
    
    user_prompt = f"Case ID: {case_id}\nQuery: {request.query}\n"
    
    try:
        response = await provider.async_generate([
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # Post-process to ensure no stars or hashes leak through
        clean_response = response.replace("*", "").replace("#", "")
        
        # Provide a mock citation to show capability
        mock_citation = {
            "document_id": "mock-doc-123",
            "title": "Extracted Graph Context"
        }
        
        return CopilotQueryResponse(
            answer=clean_response,
            citations=[mock_citation]
        )
    except Exception as e:
        return CopilotQueryResponse(
            answer=f"Error generating intelligence response: {str(e)}\n\nPlease ensure your OPENAI_API_KEY environment variable is configured correctly.",
            citations=[]
        )
