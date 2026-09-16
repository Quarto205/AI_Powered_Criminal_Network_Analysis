"""
Rapid Fan-In / Fan-Out Detector
"""
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from agents.intelligence.base_detector import BaseDetector
from agents.intelligence.models import AlertCandidate
from agents.intelligence.thresholds import PatternThresholds
from agents.intelligence.temporal import validate_timestamps, safe_time_difference_hours, TemporalSafetyError, INSUFFICIENT_TEMPORAL_DATA
from backend.db.models.entities import Transaction

logger = logging.getLogger(__name__)

class FanInFanOutDetector(BaseDetector):
    def detect(self) -> List[AlertCandidate]:
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.sender.has(case_id=self.case_id))
            .all()
        )
        
        # Group by sender (for fan-out) and receiver (for fan-in)
        fan_out_map: Dict[str, List[Transaction]] = defaultdict(list)
        fan_in_map: Dict[str, List[Transaction]] = defaultdict(list)
        
        for tx in transactions:
            fan_out_map[str(tx.sender_ref)].append(tx)
            fan_in_map[str(tx.receiver_ref)].append(tx)
            
        self._detect_rapid_pattern(
            fan_out_map,
            PatternThresholds.FAN_OUT_MIN_DEGREE,
            "RAPID_FAN_OUT",
            "source"
        )
        
        self._detect_rapid_pattern(
            fan_in_map,
            PatternThresholds.FAN_IN_MIN_DEGREE,
            "RAPID_FAN_IN",
            "target"
        )
        
        return self.alerts

    def _detect_rapid_pattern(
        self, 
        tx_map: Dict[str, List[Transaction]], 
        min_degree: int, 
        alert_type: str,
        focal_role: str
    ):
        for focal_node, txs in tx_map.items():
            if len(txs) < min_degree:
                continue
                
            try:
                # Extract and validate timestamps
                timestamps = [t.time for t in txs]
                validate_timestamps(timestamps)
                
                # Sort transactions by time
                sorted_txs = sorted(txs, key=lambda t: t.time)
                
                # Sliding window to find dense clusters
                # A dense cluster is `min_degree` transactions within FAN_WINDOW_HOURS
                found_clusters = []
                n = len(sorted_txs)
                for i in range(n - min_degree + 1):
                    window = sorted_txs[i:i+min_degree]
                    diff_hours = safe_time_difference_hours(window[0].time, window[-1].time)
                    
                    if diff_hours <= PatternThresholds.FAN_WINDOW_HOURS:
                        # We found a rapid burst. Collect unique counterparties
                        if focal_role == "source":
                            counterparties = set(str(tx.receiver_ref) for tx in window)
                        else:
                            counterparties = set(str(tx.sender_ref) for tx in window)
                            
                        # Avoid duplicate transactions to the same counterparty inflating the degree
                        if len(counterparties) >= min_degree:
                            found_clusters.append(window)
                            
                # Report each disjoint or overlapping cluster, or just take the maximum one.
                # For simplicity, we just take the first one found per focal node to avoid alert spam.
                if found_clusters:
                    best_cluster = found_clusters[0]
                    tx_ids = [str(tx.transaction_id) for tx in best_cluster]
                    if focal_role == "source":
                        counterparties = list(set(str(tx.receiver_ref) for tx in best_cluster))
                    else:
                        counterparties = list(set(str(tx.sender_ref) for tx in best_cluster))
                        
                    self.alerts.append(AlertCandidate(
                        case_id=str(self.case_id),
                        rule_id="FAN_IN_OUT",
                        alert_type=alert_type,
                        severity="MEDIUM",
                        contributing_entities={
                            "focal_node": focal_node,
                            "counterparties": counterparties,
                            "transactions": tx_ids
                        },
                        metadata={
                            "window_start": best_cluster[0].time.isoformat(),
                            "window_end": best_cluster[-1].time.isoformat(),
                            "unique_counterparties_count": len(counterparties),
                            "parameters": {
                                "window_hours": PatternThresholds.FAN_WINDOW_HOURS,
                                "min_degree": min_degree
                            }
                        }
                    ))
                    
            except TemporalSafetyError as e:
                if str(e) == INSUFFICIENT_TEMPORAL_DATA:
                    logger.warning(f"Insufficient temporal data for {alert_type} on node {focal_node}.")
                    self.alerts.append(AlertCandidate(
                        case_id=str(self.case_id),
                        rule_id="FAN_IN_OUT",
                        alert_type=INSUFFICIENT_TEMPORAL_DATA,
                        severity="LOW",
                        contributing_entities={"focal_node": focal_node, "transactions": [str(t.transaction_id) for t in txs]},
                        metadata={"reason": "Missing or malformed timestamps in fan-in/fan-out evaluation"}
                    ))
