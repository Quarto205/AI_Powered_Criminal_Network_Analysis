"""
Dempster-Shafer / Subjective Logic Belief Engine
Handles mathematical combination of independent evidence sources.

Frame of Discernment: Θ = {SUPPORTED, NOT_SUPPORTED}
Mass values:
b = m({SUPPORTED})
d = m({NOT_SUPPORTED})
u = m(Θ)
"""
from typing import Tuple

TOLERANCE = 1e-5

def validate_mass(b: float, d: float, u: float) -> None:
    """Validates the belief mass tuple within tolerance."""
    if not (0.0 <= b <= 1.0 + TOLERANCE):
        raise ValueError(f"Belief {b} is out of bounds")
    if not (0.0 <= d <= 1.0 + TOLERANCE):
        raise ValueError(f"Disbelief {d} is out of bounds")
    if not (0.0 <= u <= 1.0 + TOLERANCE):
        raise ValueError(f"Uncertainty {u} is out of bounds")
    
    total = b + d + u
    if abs(total - 1.0) > TOLERANCE:
        raise ValueError(f"Belief masses must sum to 1.0, got {total}")

def evidence_to_mass(confidence: float, is_supportive: bool = True, base_uncertainty: float = 0.1) -> Tuple[float, float, float]:
    """
    Maps a raw signal confidence to a Dempster-Shafer mass tuple (b, d, u).
    confidence: value in [0, 1] representing the strength of the evidence signal.
    is_supportive: True if evidence supports the relationship, False if it contradicts.
    base_uncertainty: minimum uncertainty to retain.
    """
    confidence = max(0.0, min(1.0, confidence))
    
    # The effective weight assigned to the specific claim
    weight = confidence * (1.0 - base_uncertainty)
    
    if is_supportive:
        b = weight
        d = 0.0
    else:
        b = 0.0
        d = weight
        
    u = 1.0 - (b + d)
    
    validate_mass(b, d, u)
    return b, d, u

def dempster_combine(m1: Tuple[float, float, float], m2: Tuple[float, float, float]) -> Tuple[float, float, float, float]:
    """
    Orthogonal combination rule for two evidence sources.
    Returns (b, d, u, K) where K is the conflict mass.
    """
    b1, d1, u1 = m1
    b2, d2, u2 = m2
    
    validate_mass(b1, d1, u1)
    validate_mass(b2, d2, u2)
    
    # Conflict mass
    K = (b1 * d2) + (b2 * d1)
    
    # If K is extremely close to 1, sources are perfectly contradicting and leave zero mass.
    if abs(K - 1.0) < TOLERANCE:
        return 0.0, 0.0, 1.0, K
        
    # Combine and normalize
    normalization = 1.0 - K
    
    b_new = ((b1 * b2) + (b1 * u2) + (b2 * u1)) / normalization
    d_new = ((d1 * d2) + (d1 * u2) + (d2 * u1)) / normalization
    u_new = (u1 * u2) / normalization
    
    validate_mass(b_new, d_new, u_new)
    
    return b_new, d_new, u_new, K
