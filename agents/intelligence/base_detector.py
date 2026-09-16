"""
Base interface for deterministic pattern detectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from agents.intelligence.models import AlertCandidate


class BaseDetector(ABC):
    """
    Abstract base class for all pattern and motif detectors.
    """

    def __init__(self, db: Session, case_id: UUID):
        self.db = db
        self.case_id = case_id
        self.alerts: List[AlertCandidate] = []

    @abstractmethod
    def detect(self) -> List[AlertCandidate]:
        """
        Executes the detection logic against the PostgreSQL database.
        Returns a list of AlertCandidate objects.
        """
        pass
