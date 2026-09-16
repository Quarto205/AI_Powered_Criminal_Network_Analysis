"""
Cross-Community Bridges Detector
"""
import logging
import networkx as nx
from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from agents.intelligence.base_detector import BaseDetector
from agents.intelligence.models import AlertCandidate
from backend.db.models.entities import Transaction, Communication
from agents.intelligence.sna_engine import SNAEngine

logger = logging.getLogger(__name__)

class CommunityBridgeDetector(BaseDetector):
    def detect(self) -> List[AlertCandidate]:
        # Query relationships
        txs = self.db.query(Transaction).filter(Transaction.sender.has(case_id=self.case_id)).all()
        comms = self.db.query(Communication).filter(Communication.caller.has(case_id=self.case_id)).all()
        
        if not txs and not comms:
            return self.alerts
            
        G = nx.Graph()
        
        for tx in txs:
            G.add_edge(str(tx.sender_ref), str(tx.receiver_ref), weight=1.0)
            
        for comm in comms:
            G.add_edge(str(comm.caller_ref), str(comm.receiver_ref), weight=1.0)
            
        if len(G) < 3:
            return self.alerts
            
        sna = SNAEngine(G)
        communities_info = sna.compute_communities()
        assignments = communities_info.get("assignments", {})
        
        # A bridge is a node that connects to multiple distinct communities
        for node in G.nodes():
            my_comm = assignments.get(node)
            if not my_comm:
                continue
                
            neighbor_comms = set()
            for neighbor in G.neighbors(node):
                n_comm = assignments.get(neighbor)
                if n_comm:
                    neighbor_comms.add(n_comm)
                    
            # If the node's neighbors span more than 1 community, it's a bridge.
            # To be a significant bridge, let's require at least 2 distinct communities among neighbors.
            if len(neighbor_comms) > 1:
                # Calculate simple participation metric
                # How many distinct communities does this node connect?
                
                # Exclude own community from bridged list to list external bridged communities
                external_comms = neighbor_comms - {my_comm}
                
                if external_comms:
                    self.alerts.append(AlertCandidate(
                        case_id=str(self.case_id),
                        rule_id="COMMUNITY_BRIDGE",
                        alert_type="CROSS_COMMUNITY_BRIDGE",
                        severity="MEDIUM",
                        contributing_entities={
                            "bridge_node": node,
                            "own_community": my_comm,
                            "bridged_communities": list(external_comms)
                        },
                        metadata={
                            "connected_communities_count": len(neighbor_comms),
                            "degree": G.degree(node),
                            "algorithm": communities_info.get("algorithm", "UNKNOWN")
                        }
                    ))
                    
        return self.alerts
