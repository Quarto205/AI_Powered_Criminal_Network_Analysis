import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.models.analytics import NetworkMetric, Alert, Prediction, RiskScore, ModelRun
from backend.db.models.entities import Entity, Relationship
from agents.intelligence.config import PriorityWeights, SeverityMapping

logger = logging.getLogger(__name__)


class PriorityEngine:
    """
    Deterministic ranking engine synthesizing Phase 1 (SNA), Phase 2 (Alerts),
    Phase 3 (Predictions), and Temporal Recency into an Investigative Priority Score.
    """
    def __init__(self, db: Session, case_id: UUID):
        self.db = db
        self.case_id = case_id

    def _get_sna_component(self) -> Dict[UUID, float]:
        """
        Retrieves Degree and Betweenness centralities, normalizes them,
        and returns the average SNA component per entity.
        """
        metrics = self.db.query(NetworkMetric).filter(
            NetworkMetric.case_id == self.case_id,
            NetworkMetric.metric_type.in_(["DEGREE_CENTRALITY", "BETWEENNESS_CENTRALITY"])
        ).all()
        
        raw_scores: Dict[UUID, List[float]] = {}
        for m in metrics:
            if m.target_entity_uuid and m.value is not None:
                if m.target_entity_uuid not in raw_scores:
                    raw_scores[m.target_entity_uuid] = []
                raw_scores[m.target_entity_uuid].append(m.value)
                
        # To avoid data leakage or cross-case bounds, if we don't have absolute bounds,
        # we assume SNA scores are already 0-1 (e.g., standard normalized degree/betweenness)
        # We cap them at 1.0 just in case.
        sna_component = {}
        for entity_id, values in raw_scores.items():
            if values:
                avg = sum(values) / len(values)
                sna_component[entity_id] = min(avg, 1.0)
        return sna_component

    def _get_alert_component(self) -> Dict[UUID, float]:
        """
        Retrieves alert severities and takes the maximum normalized severity per entity.
        """
        alerts = self.db.query(Alert).filter(Alert.case_id == self.case_id).all()
        
        entity_severities: Dict[UUID, float] = {}
        for alert in alerts:
            val = SeverityMapping.MAPPING.get(alert.severity.upper(), 0.0)
            if alert.contributing_entities:
                # Expecting dictionary of roles to canonical strings/UUIDs, or just list
                # For safety, let's assume contributing_entities might contain IDs.
                # Actually, in Phase 2, contributing_entities usually contains entity_id -> details
                for entity_id_str in alert.contributing_entities.keys():
                    try:
                        eid = UUID(entity_id_str)
                        if eid not in entity_severities or val > entity_severities[eid]:
                            entity_severities[eid] = val
                    except ValueError:
                        continue
        return entity_severities

    def _get_gatv2_component(self) -> Dict[UUID, float]:
        """
        Retrieves the maximum GATv2 prediction score for each entity.
        """
        predictions = self.db.query(Prediction).filter(
            Prediction.case_id == self.case_id,
            Prediction.status == "INFERRED"
        ).all()
        
        gat_component: Dict[UUID, float] = {}
        for pred in predictions:
            # Score applies to both source and target as investigative leads
            for eid in (pred.source_ref, pred.target_ref):
                if eid not in gat_component or pred.score > gat_component[eid]:
                    gat_component[eid] = min(pred.score, 1.0)
        return gat_component

    def _get_temporal_component(self) -> Dict[UUID, float]:
        """
        Calculates recency decay based on the most recent observed relationship timestamp.
        """
        # Find most recent relationship per entity
        now = datetime.now(timezone.utc)
        
        rels = self.db.query(Relationship).filter(
            Relationship.case_id == self.case_id,
            Relationship.status == "OBSERVED"
        ).all()
        
        latest_time: Dict[UUID, datetime] = {}
        for rel in rels:
            if not rel.created_at:
                continue
            for eid in (rel.source_entity_uuid, rel.target_entity_uuid):
                if eid not in latest_time or rel.created_at > latest_time[eid]:
                    latest_time[eid] = rel.created_at
                    
        temporal_component: Dict[UUID, float] = {}
        for eid, ts in latest_time.items():
            # ensure tz aware
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_days = (now - ts).total_seconds() / 86400.0
            if age_days < 0:
                age_days = 0  # prevent future leakage artifacts
            temporal_component[eid] = math.exp(-PriorityWeights.TEMPORAL_DECAY_LAMBDA * age_days)
            
        return temporal_component

    def run_priority_ranking(self) -> List[RiskScore]:
        """
        Synthesizes the four components for all entities in the case.
        Returns the unsaved RiskScore instances.
        """
        entities = self.db.query(Entity).filter(
            Entity.case_id == self.case_id,
            Entity.status == "ACTIVE"
        ).all()
        
        if not entities:
            return []

        sna_comp = self._get_sna_component()
        alert_comp = self._get_alert_component()
        gat_comp = self._get_gatv2_component()
        temporal_comp = self._get_temporal_component()
        
        run_id = uuid4()
        model_run = ModelRun(
            run_id=run_id,
            model_name="PriorityEngine",
            version="1.0",
            task_type="INVESTIGATIVE_RANKING",
            input_snapshot_checksum="N/A",  # Not strictly snapshot bound
            status="COMPLETED"
        )
        self.db.add(model_run)
        
        risk_scores = []
        
        for entity in entities:
            eid = entity.entity_id
            
            sna_val = sna_comp.get(eid, 0.0)
            alert_val = alert_comp.get(eid, 0.0)
            gat_val = gat_comp.get(eid, 0.0)
            temporal_val = temporal_comp.get(eid, 0.0)
            
            score = (
                sna_val * PriorityWeights.SNA_WEIGHT +
                alert_val * PriorityWeights.ALERT_WEIGHT +
                gat_val * PriorityWeights.GAT_WEIGHT +
                temporal_val * PriorityWeights.TEMPORAL_WEIGHT
            )
            
            if score == 0.0:
                continue # Do not create zero-priority leads unless required. We'll skip for efficiency.
                
            rs = RiskScore(
                score_id=uuid4(),
                target_entity_uuid=eid,
                run_id=run_id,
                score_type="PRIORITY_RANKING",
                value=score,
                features_summary={
                    "components": {
                        "sna_centrality": sna_val,
                        "alert_severity": alert_val,
                        "gatv2_score": gat_val,
                        "temporal_recency": temporal_val
                    },
                    "contributions": {
                        "sna_centrality": sna_val * PriorityWeights.SNA_WEIGHT,
                        "alert_severity": alert_val * PriorityWeights.ALERT_WEIGHT,
                        "gatv2_score": gat_val * PriorityWeights.GAT_WEIGHT,
                        "temporal_recency": temporal_val * PriorityWeights.TEMPORAL_WEIGHT
                    },
                    "missing_data": {
                        "sna": eid not in sna_comp,
                        "alert": eid not in alert_comp,
                        "gatv2": eid not in gat_comp,
                        "temporal": eid not in temporal_comp
                    }
                }
            )
            risk_scores.append(rs)
            
        # Deterministic sorting: primary=score desc, secondary=entity_id str desc
        risk_scores.sort(key=lambda x: (x.value, str(x.target_entity_uuid)), reverse=True)
        
        for rs in risk_scores:
            self.db.add(rs)
            
        self.db.flush()
        return risk_scores
