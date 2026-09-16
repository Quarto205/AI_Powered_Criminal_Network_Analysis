"""
Communication Burst Detector
"""
import logging
from typing import List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from agents.intelligence.base_detector import BaseDetector
from agents.intelligence.models import AlertCandidate
from agents.intelligence.thresholds import PatternThresholds
from agents.intelligence.temporal import validate_timestamps, TemporalSafetyError, INSUFFICIENT_TEMPORAL_DATA
from backend.db.models.entities import Communication, Event

logger = logging.getLogger(__name__)

class CommunicationBurstDetector(BaseDetector):
    def detect(self) -> List[AlertCandidate]:
        # Query incidents (events)
        incidents = (
            self.db.query(Event)
            .filter(Event.case_id == self.case_id)
            .all()
        )
        
        # Query all communications to scan for bursts
        comms = (
            self.db.query(Communication)
            .filter(Communication.caller.has(case_id=self.case_id))
            .all()
        )
        
        if not comms or not incidents:
            return self.alerts
            
        try:
            # Validate timestamps
            incident_times = validate_timestamps([inc.timestamp for inc in incidents])
            comm_times = validate_timestamps([c.timestamps for c in comms])
        except TemporalSafetyError as e:
            if str(e) == INSUFFICIENT_TEMPORAL_DATA:
                logger.warning("Insufficient temporal data for communication burst evaluation.")
                self.alerts.append(AlertCandidate(
                    case_id=str(self.case_id),
                    rule_id="COMM_BURST",
                    alert_type=INSUFFICIENT_TEMPORAL_DATA,
                    severity="LOW",
                    contributing_entities={},
                    metadata={"reason": "Missing or malformed timestamps in events or communications"}
                ))
            return self.alerts

        for inc, inc_time in zip(incidents, incident_times):
            # Define windows
            baseline_start = inc_time - timedelta(hours=PatternThresholds.COMM_BURST_BASELINE_WINDOW_HOURS + PatternThresholds.COMM_BURST_INCIDENT_WINDOW_BEFORE_HOURS)
            baseline_end = inc_time - timedelta(hours=PatternThresholds.COMM_BURST_INCIDENT_WINDOW_BEFORE_HOURS)
            
            burst_start = inc_time - timedelta(hours=PatternThresholds.COMM_BURST_INCIDENT_WINDOW_BEFORE_HOURS)
            burst_end = inc_time + timedelta(hours=PatternThresholds.COMM_BURST_INCIDENT_WINDOW_AFTER_HOURS)
            
            baseline_comms = [c for c, c_time in zip(comms, comm_times) if baseline_start <= c_time < baseline_end]
            burst_comms = [c for c, c_time in zip(comms, comm_times) if burst_start <= c_time <= burst_end]
            
            if len(burst_comms) < PatternThresholds.COMM_BURST_MIN_EVENTS:
                continue
                
            baseline_hours = PatternThresholds.COMM_BURST_BASELINE_WINDOW_HOURS
            burst_hours = PatternThresholds.COMM_BURST_INCIDENT_WINDOW_BEFORE_HOURS + PatternThresholds.COMM_BURST_INCIDENT_WINDOW_AFTER_HOURS
            
            baseline_rate = len(baseline_comms) / baseline_hours if baseline_hours > 0 else 0
            burst_rate = len(burst_comms) / burst_hours if burst_hours > 0 else 0
            
            # Deterministic threshold: burst_rate must be > baseline_rate * multiplier
            # If baseline_rate is 0, we can fall back to checking if burst_events > min_events
            is_burst = False
            if baseline_rate > 0:
                is_burst = burst_rate >= baseline_rate * PatternThresholds.COMM_BURST_MULTIPLIER
            else:
                is_burst = True # Spiking from 0 to something above min_events
                
            if is_burst:
                comm_ids = [str(c.communication_id) for c in burst_comms]
                involved_entities = list(set([str(c.caller_ref) for c in burst_comms] + [str(c.receiver_ref) for c in burst_comms]))
                
                self.alerts.append(AlertCandidate(
                    case_id=str(self.case_id),
                    rule_id="COMM_BURST",
                    alert_type="COMMUNICATION_BURST",
                    severity="HIGH",
                    contributing_entities={
                        "incident_event": str(inc.event_id),
                        "communications": comm_ids,
                        "entities": involved_entities
                    },
                    metadata={
                        "incident_timestamp": inc_time.isoformat(),
                        "window_start": burst_start.isoformat(),
                        "window_end": burst_end.isoformat(),
                        "baseline_count": len(baseline_comms),
                        "burst_count": len(burst_comms),
                        "parameters": {
                            "baseline_window_hours": baseline_hours,
                            "burst_window_hours": burst_hours,
                            "multiplier": PatternThresholds.COMM_BURST_MULTIPLIER
                        }
                    }
                ))

        return self.alerts
