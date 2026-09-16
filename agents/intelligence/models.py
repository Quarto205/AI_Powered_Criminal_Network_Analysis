"""
Data models for the Pattern & Motif Engine.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List
import hashlib
import json

@dataclass
class AlertCandidate:
    case_id: str
    rule_id: str
    alert_type: str
    severity: str
    contributing_entities: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def generate_fingerprint(self) -> str:
        """
        Generates a deterministic SHA256 fingerprint from the rule, case, and canonical entities.
        """
        # Canonicalize entities by sorting dict keys and values deterministically
        ent_str = json.dumps(self.contributing_entities, sort_keys=True)
        # Canonicalize specific metadata parameters that define uniqueness (e.g., specific event window)
        # We don't hash the entire metadata to avoid timestamp variations changing the fingerprint if not intended,
        # but window start/end is important if available.
        window_start = self.metadata.get("window_start", "")
        window_end = self.metadata.get("window_end", "")
        
        raw = f"{self.case_id}|{self.rule_id}|{ent_str}|{window_start}|{window_end}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Converts to a dictionary suitable for AlertRepository."""
        meta = dict(self.metadata)
        meta["fingerprint"] = self.generate_fingerprint()
        return {
            "case_id": self.case_id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "contributing_entities": self.contributing_entities,
            "metadata_": meta,
        }
