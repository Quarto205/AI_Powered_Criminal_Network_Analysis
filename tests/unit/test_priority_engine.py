import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
import math

from agents.intelligence.priority_engine import PriorityEngine
from agents.intelligence.config import PriorityWeights
from backend.db.models.analytics import RiskScore

def test_priority_engine_formula_and_determinism():
    """
    Given known mocked inputs, verifies that the final score strictly adheres
    to the configured weights formula.
    """
    db = MagicMock()
    case_id = uuid4()
    engine = PriorityEngine(db, case_id)
    
    entity_id = uuid4()
    
    # Mock the component retrieval functions
    engine._get_sna_component = MagicMock(return_value={entity_id: 0.8})
    engine._get_alert_component = MagicMock(return_value={entity_id: 0.66}) # MEDIUM
    engine._get_gatv2_component = MagicMock(return_value={entity_id: 0.9})
    
    now = datetime.now(timezone.utc)
    engine._get_temporal_component = MagicMock(return_value={entity_id: 1.0})
    
    # Mock entities lookup
    mock_entity = MagicMock()
    mock_entity.entity_id = entity_id
    db.query().filter().all.return_value = [mock_entity]
    
    scores = engine.run_priority_ranking()
    assert len(scores) == 1
    
    expected_score = (
        0.8 * PriorityWeights.SNA_WEIGHT +
        0.66 * PriorityWeights.ALERT_WEIGHT +
        0.9 * PriorityWeights.GAT_WEIGHT +
        1.0 * PriorityWeights.TEMPORAL_WEIGHT
    )
    
    assert math.isclose(scores[0].value, expected_score, rel_tol=1e-5)
    assert scores[0].target_entity_uuid == entity_id
    assert scores[0].score_type == "PRIORITY_RANKING"

def test_priority_engine_ordering_and_tie_break():
    """
    Verifies that highest scores are first, and ties use entity_id for stable determinism.
    """
    db = MagicMock()
    case_id = uuid4()
    engine = PriorityEngine(db, case_id)
    
    # Three entities: 
    # e1: high score
    # e2, e3: same lower score
    # We will set their UUIDs so e2 < e3 stringwise.
    e1_id = uuid4()
    e2_id = uuid4()
    e3_id = uuid4()
    
    # Ensure stable ordering for e2 and e3
    if str(e2_id) > str(e3_id):
        e2_id, e3_id = e3_id, e2_id

    engine._get_sna_component = MagicMock(return_value={e1_id: 1.0, e2_id: 0.5, e3_id: 0.5})
    engine._get_alert_component = MagicMock(return_value={e1_id: 1.0, e2_id: 0.5, e3_id: 0.5})
    engine._get_gatv2_component = MagicMock(return_value={e1_id: 1.0, e2_id: 0.5, e3_id: 0.5})
    engine._get_temporal_component = MagicMock(return_value={e1_id: 1.0, e2_id: 0.5, e3_id: 0.5})

    m1, m2, m3 = MagicMock(), MagicMock(), MagicMock()
    m1.entity_id = e1_id
    m2.entity_id = e2_id
    m3.entity_id = e3_id
    
    db.query().filter().all.return_value = [m1, m2, m3]
    
    scores = engine.run_priority_ranking()
    assert len(scores) == 3
    
    # Rank 1: e1
    assert scores[0].target_entity_uuid == e1_id
    
    # Rank 2/3 tie break. Since e2 < e3, and reverse=True, e3_id should come before e2_id
    # Wait, the sorting key is `(value, str(entity_id))`, `reverse=True`. 
    # Therefore, highest value first. If value is same, highest string first.
    # We ensured e2 < e3, so e3 should be first (rank 2).
    assert scores[1].target_entity_uuid == e3_id
    assert scores[2].target_entity_uuid == e2_id

def test_missing_data_behavior():
    """
    Verifies that missing data translates to 0.0 contribution rather than errors.
    """
    db = MagicMock()
    case_id = uuid4()
    engine = PriorityEngine(db, case_id)
    
    entity_id = uuid4()
    
    # E1 has only SNA, nothing else.
    engine._get_sna_component = MagicMock(return_value={entity_id: 0.8})
    engine._get_alert_component = MagicMock(return_value={}) 
    engine._get_gatv2_component = MagicMock(return_value={})
    engine._get_temporal_component = MagicMock(return_value={})
    
    mock_entity = MagicMock()
    mock_entity.entity_id = entity_id
    db.query().filter().all.return_value = [mock_entity]
    
    scores = engine.run_priority_ranking()
    
    expected_score = 0.8 * PriorityWeights.SNA_WEIGHT
    assert math.isclose(scores[0].value, expected_score, rel_tol=1e-5)
    
    feats = scores[0].features_summary
    assert feats["missing_data"]["alert"] is True
    assert feats["missing_data"]["gatv2"] is True
    assert feats["missing_data"]["temporal"] is True
    assert feats["missing_data"]["sna"] is False
