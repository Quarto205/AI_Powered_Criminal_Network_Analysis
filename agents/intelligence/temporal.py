"""
Temporal safety mechanisms.
Enforces the mandatory invariant: missing or malformed timestamps yield INSUFFICIENT_TEMPORAL_DATA.
"""

from typing import Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

INSUFFICIENT_TEMPORAL_DATA = "INSUFFICIENT_TEMPORAL_DATA"

class TemporalSafetyError(Exception):
    """Raised when temporal requirements cannot be safely met."""
    pass

def validate_timestamps(timestamps: List[Any]) -> List[datetime]:
    """
    Validates a list of required timestamps.
    If any timestamp is missing, null, or unparseable, raises TemporalSafetyError.
    Normalizes to UTC datetime objects.
    """
    parsed = []
    for ts in timestamps:
        if not ts:
            logger.warning(f"Temporal safety failed: missing timestamp.")
            raise TemporalSafetyError(INSUFFICIENT_TEMPORAL_DATA)
        
        if isinstance(ts, datetime):
            parsed.append(ts)
        elif isinstance(ts, str):
            try:
                # Handle isoformat strings. Replace Z with +00:00 for python < 3.11 compat if needed,
                # but standard fromisoformat usually works in 3.11+.
                ts_str = ts.replace("Z", "+00:00")
                parsed.append(datetime.fromisoformat(ts_str))
            except ValueError:
                logger.warning(f"Temporal safety failed: unparseable timestamp {ts}.")
                raise TemporalSafetyError(INSUFFICIENT_TEMPORAL_DATA)
        else:
            logger.warning(f"Temporal safety failed: invalid type {type(ts)}.")
            raise TemporalSafetyError(INSUFFICIENT_TEMPORAL_DATA)
            
    return parsed

def safe_time_difference_hours(start: datetime, end: datetime) -> float:
    """
    Safely calculates hours between two validated datetimes.
    If start > end, this is ambiguous/invalid ordering for a sequence, raises error.
    """
    if start > end:
        logger.warning("Temporal safety failed: out-of-order timestamps.")
        raise TemporalSafetyError(INSUFFICIENT_TEMPORAL_DATA)
        
    diff = end - start
    return diff.total_seconds() / 3600.0
