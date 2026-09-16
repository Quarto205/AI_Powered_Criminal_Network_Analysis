"""
Configuration for Phase 4: Priority Ranking Engine and Explanations.
"""

class PriorityWeights:
    """
    Configurable weights for the priority ranking formula.
    These should sum to 1.0 for normalized interpretation.
    """
    SNA_WEIGHT = 0.25
    ALERT_WEIGHT = 0.25
    GAT_WEIGHT = 0.25
    TEMPORAL_WEIGHT = 0.25

    # Temporal decay lambda (e.g., 0.01 decay per day)
    # Recency = exp(-lambda * age_in_days)
    TEMPORAL_DECAY_LAMBDA = 0.01

class SeverityMapping:
    """
    Maps alert severities to deterministic normalized values [0, 1].
    """
    MAPPING = {
        "LOW": 0.33,
        "MEDIUM": 0.66,
        "HIGH": 1.0,
        "CRITICAL": 1.0
    }
