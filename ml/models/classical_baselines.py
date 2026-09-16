import networkx as nx
from typing import Dict, List, Tuple

class ClassicalBaselines:
    """
    Computes classical link prediction heuristics over a given graph.
    All methods expect a NetworkX undirected graph for these structural metrics.
    Handles isolated/zero-degree nodes safely.
    """
    def __init__(self, graph: nx.Graph):
        # We enforce an undirected view because standard PA, CN, Jaccard, etc.,
        # are fundamentally defined for undirected networks in standard benchmarks.
        if graph.is_directed():
            self.graph = graph.to_undirected(as_view=True)
        else:
            self.graph = graph

    def compute_all(self, ebunch: List[Tuple[str, str]]) -> Dict[Tuple[str, str], Dict[str, float]]:
        """
        Computes Common Neighbors, Jaccard, Adamic-Adar, Preferential Attachment, and Resource Allocation
        for a list of node pairs (u, v).
        Returns a dictionary mapping (u, v) to a dictionary of metric scores.
        """
        # Validate that all nodes exist in the graph to prevent KeyErrors
        valid_ebunch = [(u, v) for u, v in ebunch if u in self.graph and v in self.graph]
        
        results = { (u, v): {} for u, v in ebunch }

        # Initialize with zeros for safety
        for u, v in ebunch:
            results[(u, v)] = {
                "common_neighbors": 0.0,
                "jaccard": 0.0,
                "adamic_adar": 0.0,
                "preferential_attachment": 0.0,
                "resource_allocation": 0.0
            }
            
        if not valid_ebunch:
            return results

        # Preferential Attachment
        preds_pa = nx.preferential_attachment(self.graph, valid_ebunch)
        for u, v, p in preds_pa:
            results[(u, v)]["preferential_attachment"] = p

        # Jaccard Coefficient
        preds_jac = nx.jaccard_coefficient(self.graph, valid_ebunch)
        for u, v, p in preds_jac:
            results[(u, v)]["jaccard"] = p

        # Adamic-Adar
        preds_aa = nx.adamic_adar_index(self.graph, valid_ebunch)
        for u, v, p in preds_aa:
            results[(u, v)]["adamic_adar"] = p

        # Resource Allocation
        preds_ra = nx.resource_allocation_index(self.graph, valid_ebunch)
        for u, v, p in preds_ra:
            results[(u, v)]["resource_allocation"] = p

        # Common Neighbors
        for u, v in valid_ebunch:
            cn = len(list(nx.common_neighbors(self.graph, u, v)))
            results[(u, v)]["common_neighbors"] = float(cn)

        return results
