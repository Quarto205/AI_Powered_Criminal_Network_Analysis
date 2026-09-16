"""
Configurable thresholds for deterministic pattern detectors.
"""

class PatternThresholds:
    # Transaction Cycles
    TX_CYCLE_MAX_LENGTH: int = 5
    TX_CYCLE_MAX_WINDOW_HOURS: int = 24
    TX_CYCLE_MIN_TRANSACTIONS: int = 3
    
    # Communication Bursts
    COMM_BURST_BASELINE_WINDOW_HOURS: int = 72
    COMM_BURST_INCIDENT_WINDOW_BEFORE_HOURS: int = 1
    COMM_BURST_INCIDENT_WINDOW_AFTER_HOURS: int = 4
    COMM_BURST_MIN_EVENTS: int = 10
    COMM_BURST_MULTIPLIER: float = 3.0
    
    # Rapid Fan-In / Fan-Out
    FAN_WINDOW_HOURS: int = 2
    FAN_OUT_MIN_DEGREE: int = 5
    FAN_IN_MIN_DEGREE: int = 5
