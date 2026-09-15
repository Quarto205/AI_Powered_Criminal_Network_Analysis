import pytest
from agents.evidence.belief_engine import evidence_to_mass, dempster_combine, validate_mass, TOLERANCE

def test_validate_mass():
    # Valid
    validate_mass(0.5, 0.3, 0.2)
    validate_mass(0.0, 0.0, 1.0)
    validate_mass(1.0, 0.0, 0.0)
    
    # Invalid bounds
    with pytest.raises(ValueError):
        validate_mass(-0.1, 0.5, 0.6)
    with pytest.raises(ValueError):
        validate_mass(0.5, 1.1, -0.6)
        
    # Invalid sum
    with pytest.raises(ValueError):
        validate_mass(0.5, 0.5, 0.5)

def test_evidence_to_mass():
    b, d, u = evidence_to_mass(1.0, is_supportive=True, base_uncertainty=0.1)
    assert abs(b - 0.9) < TOLERANCE
    assert abs(d - 0.0) < TOLERANCE
    assert abs(u - 0.1) < TOLERANCE
    
    b, d, u = evidence_to_mass(1.0, is_supportive=False, base_uncertainty=0.1)
    assert abs(b - 0.0) < TOLERANCE
    assert abs(d - 0.9) < TOLERANCE
    assert abs(u - 0.1) < TOLERANCE
    
    b, d, u = evidence_to_mass(0.5, is_supportive=True, base_uncertainty=0.2)
    assert abs(b - 0.4) < TOLERANCE
    assert abs(d - 0.0) < TOLERANCE
    assert abs(u - 0.6) < TOLERANCE

def test_dempster_combine_two_supportive():
    m1 = (0.5, 0.0, 0.5)
    m2 = (0.5, 0.0, 0.5)
    
    b, d, u, K = dempster_combine(m1, m2)
    assert K == 0.0
    # b_new = (0.25 + 0.25 + 0.25) / 1.0 = 0.75
    assert abs(b - 0.75) < TOLERANCE
    assert d == 0.0
    assert abs(u - 0.25) < TOLERANCE

def test_dempster_combine_conflict():
    m1 = (0.8, 0.0, 0.2)
    m2 = (0.0, 0.8, 0.2)
    
    b, d, u, K = dempster_combine(m1, m2)
    # K = 0.8 * 0.8 = 0.64
    assert abs(K - 0.64) < TOLERANCE
    
    norm = 1.0 - 0.64
    assert abs(norm - 0.36) < TOLERANCE
    
    # b_new = (0 + 0.8 * 0.2 + 0) / 0.36 = 0.16 / 0.36 = 0.4444...
    assert abs(b - 0.444444) < 1e-4
    assert abs(d - 0.444444) < 1e-4
    assert abs(u - (0.04 / 0.36)) < 1e-4

def test_dempster_combine_perfect_conflict():
    m1 = (1.0, 0.0, 0.0)
    m2 = (0.0, 1.0, 0.0)
    
    b, d, u, K = dempster_combine(m1, m2)
    assert abs(K - 1.0) < TOLERANCE
    # When K=1, it should fallback to ignorance
    assert b == 0.0
    assert d == 0.0
    assert abs(u - 1.0) < TOLERANCE

def test_dempster_combine_identity():
    m1 = (0.6, 0.2, 0.2)
    ignorance = (0.0, 0.0, 1.0)
    
    b, d, u, K = dempster_combine(m1, ignorance)
    assert K == 0.0
    assert b == 0.6
    assert d == 0.2
    assert u == 0.2
