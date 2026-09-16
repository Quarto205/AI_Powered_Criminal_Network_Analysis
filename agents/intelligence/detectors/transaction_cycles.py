"""
Transaction Cycle Detector
"""
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from agents.intelligence.base_detector import BaseDetector
from agents.intelligence.models import AlertCandidate
from agents.intelligence.thresholds import PatternThresholds
from agents.intelligence.temporal import validate_timestamps, safe_time_difference_hours, TemporalSafetyError, INSUFFICIENT_TEMPORAL_DATA
from backend.db.models.entities import Transaction

logger = logging.getLogger(__name__)

class TransactionCycleDetector(BaseDetector):
    def detect(self) -> List[AlertCandidate]:
        # Query all transactions for the case
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.sender.has(case_id=self.case_id))
            .all()
        )
        
        # Build adjacency list: node -> list of (target, tx)
        adj: Dict[str, List[Tuple[str, Transaction]]] = defaultdict(list)
        for tx in transactions:
            adj[str(tx.sender_ref)].append((str(tx.receiver_ref), tx))
            
        cycles_found = []
        visited_paths = set()
        
        def dfs(current_node: str, start_node: str, path: List[Transaction], depth: int):
            if depth > PatternThresholds.TX_CYCLE_MAX_LENGTH:
                return
                
            for nxt, tx in adj[current_node]:
                # Avoid reusing the exact same transaction in a path
                if any(p.transaction_id == tx.transaction_id for p in path):
                    continue
                    
                new_path = path + [tx]
                
                if nxt == start_node and len(new_path) >= PatternThresholds.TX_CYCLE_MIN_TRANSACTIONS:
                    # Potential cycle found
                    try:
                        # Extract and validate timestamps centrally
                        timestamps = [p.time for p in new_path]
                        valid_ts = validate_timestamps(timestamps)
                        
                        # Check monotonically increasing
                        is_ordered = True
                        for i in range(len(valid_ts) - 1):
                            if valid_ts[i] > valid_ts[i+1]:
                                is_ordered = False
                                break
                                
                        if not is_ordered:
                            continue
                            
                        # Check window
                        diff_hours = safe_time_difference_hours(valid_ts[0], valid_ts[-1])
                        if diff_hours <= PatternThresholds.TX_CYCLE_MAX_WINDOW_HOURS:
                            # Canonicalize to avoid duplicates (e.g. A->B->C->A vs B->C->A->B)
                            tx_ids = sorted([str(p.transaction_id) for p in new_path])
                            cycle_hash = "-".join(tx_ids)
                            if cycle_hash not in visited_paths:
                                visited_paths.add(cycle_hash)
                                cycles_found.append(new_path)
                    except TemporalSafetyError as e:
                        if str(e) == INSUFFICIENT_TEMPORAL_DATA:
                            # We create a special candidate indicating temporal failure if needed,
                            # or just skip. The prompt says "If one timestamp is missing... Do not generate the transaction-cycle alert."
                            # But wait, it says "Instead produce: INSUFFICIENT_TEMPORAL_DATA... No: assume timestamp -> generate suspicious alert".
                            # If we just skip, we don't produce a normal alert. We can create an alert with type INSUFFICIENT_TEMPORAL_DATA
                            # to explicitly log it, but usually skipping is enough.
                            # Let's create an INSUFFICIENT_TEMPORAL_DATA alert to be explicit!
                            # Wait, the prompt says "produce: INSUFFICIENT_TEMPORAL_DATA". We will yield an alert candidate for it.
                            logger.warning("Insufficient temporal data for transaction cycle.")
                            cycle_hash = "-".join(sorted([str(p.transaction_id) for p in new_path]))
                            if cycle_hash not in visited_paths:
                                visited_paths.add(cycle_hash)
                                self.alerts.append(AlertCandidate(
                                    case_id=str(self.case_id),
                                    rule_id="TX_CYCLE",
                                    alert_type=INSUFFICIENT_TEMPORAL_DATA,
                                    severity="LOW",
                                    contributing_entities={"transactions": [str(p.transaction_id) for p in new_path]},
                                    metadata={"reason": "Missing or malformed timestamps in cycle"}
                                ))
                            continue
                        
                else:
                    dfs(nxt, start_node, new_path, depth + 1)
                    
        for node in list(adj.keys()):
            dfs(node, node, [], 1)
            
        for cycle in cycles_found:
            tx_ids = [str(tx.transaction_id) for tx in cycle]
            entities = list(set([str(tx.sender_ref) for tx in cycle] + [str(tx.receiver_ref) for tx in cycle]))
            
            self.alerts.append(AlertCandidate(
                case_id=str(self.case_id),
                rule_id="TX_CYCLE",
                alert_type="TRANSACTION_CYCLE",
                severity="HIGH",
                contributing_entities={
                    "transactions": tx_ids,
                    "entities": entities
                },
                metadata={
                    "window_start": cycle[0].time.isoformat() if cycle[0].time else None,
                    "window_end": cycle[-1].time.isoformat() if cycle[-1].time else None,
                    "cycle_length": len(cycle),
                    "parameters": {
                        "max_window_hours": PatternThresholds.TX_CYCLE_MAX_WINDOW_HOURS,
                        "min_transactions": PatternThresholds.TX_CYCLE_MIN_TRANSACTIONS
                    }
                }
            ))
            
        return self.alerts
