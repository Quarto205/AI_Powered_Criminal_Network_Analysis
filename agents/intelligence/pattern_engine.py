"""
Pattern Engine for Agent 3 Phase 2.
Orchestrates the execution of all deterministic detectors and persists the results.
"""

import logging
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from backend.repositories.alert_repository import AlertRepository

logger = logging.getLogger(__name__)

class PatternEngine:
    """
    Coordinates execution of all deterministic detectors and handles safe persistence.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.alert_repo = AlertRepository(db)

    def run_all_detectors(self, case_id: UUID) -> dict:
        """
        Executes all active detectors for a given case and safely persists deduplicated alerts.
        """
        logger.info(f"Starting PatternEngine for case {case_id}")
        
        # Import inside to avoid circular dependencies if any
        from agents.intelligence.detectors.transaction_cycles import TransactionCycleDetector
        from agents.intelligence.detectors.communication_bursts import CommunicationBurstDetector
        from agents.intelligence.detectors.fan_in_fan_out import FanInFanOutDetector
        from agents.intelligence.detectors.community_bridges import CommunityBridgeDetector

        detectors = [
            TransactionCycleDetector(self.db, case_id),
            CommunicationBurstDetector(self.db, case_id),
            FanInFanOutDetector(self.db, case_id),
            CommunityBridgeDetector(self.db, case_id)
        ]

        all_candidates = []
        for detector in detectors:
            detector_name = detector.__class__.__name__
            try:
                candidates = detector.detect()
                all_candidates.extend(candidates)
                logger.info(f"{detector_name} generated {len(candidates)} alert candidates.")
            except Exception as e:
                logger.error(f"Error in {detector_name} for case {case_id}: {e}", exc_info=True)

        # Persist and deduplicate
        dicts = [cand.to_dict() for cand in all_candidates]
        new_alerts = self.alert_repo.save_alerts_idempotent(case_id, dicts)
        
        logger.info(f"PatternEngine completed. {len(new_alerts)} new unique alerts persisted.")
        return {
            "total_candidates": len(all_candidates),
            "new_alerts_persisted": len(new_alerts)
        }
