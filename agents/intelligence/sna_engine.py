"""
Agent 3 Phase 1: Classical SNA Analytics Engine.
Calculates deterministic structural network metrics from an extracted NetworkX graph.
Does not mutate the graph or connect to PostgreSQL/Neo4j.
"""

import networkx as nx
from typing import Dict, List, Any, Optional

try:
    from networkx.algorithms.community import louvain_communities
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    from networkx.algorithms.community import label_propagation_communities

class SNAEngine:
    """
    Independent engine for calculating classical Social Network Analysis metrics.
    """
    
    def __init__(self, graph: nx.Graph):
        """
        Initializes the SNA Engine with a NetworkX graph or DiGraph.
        """
        self.graph = graph
        self.is_directed = self.graph.is_directed()

    def get_undirected_view(self) -> nx.Graph:
        """Returns an undirected view of the graph, required for certain metrics."""
        return self.graph.to_undirected(as_view=True) if self.is_directed else self.graph

    def get_components(self) -> Dict[str, Any]:
        """
        Calculates Connected Components on the UNDIRECTED structural view.
        Returns component count, component ID per entity, and component sizes.
        """
        undirected_G = self.get_undirected_view()
        components = list(nx.connected_components(undirected_G))
        
        # Sort components deterministically by size (descending), then by smallest node id (ascending)
        components_sorted = sorted(components, key=lambda c: (-len(c), min(c) if c else ""))
        
        component_assignments = {}
        component_sizes = {}
        isolated_nodes = []
        
        for idx, comp in enumerate(components_sorted):
            comp_id = f"COMPONENT_{idx+1}"
            comp_size = len(comp)
            component_sizes[comp_id] = comp_size
            
            if comp_size == 1:
                isolated_nodes.extend(list(comp))
                
            for node in comp:
                component_assignments[node] = comp_id
                
        return {
            "component_count": len(components),
            "component_assignments": component_assignments,
            "component_sizes": component_sizes,
            "isolated_nodes": isolated_nodes
        }

    def compute_degree_centrality(self) -> Dict[str, float]:
        """
        Computes Degree Centrality.
        Uses undirected view as degree is typically interpreted as total contacts in this domain.
        Normalized by default in NetworkX.
        """
        undirected_G = self.get_undirected_view()
        if len(undirected_G) <= 1:
            return {n: 0.0 for n in undirected_G.nodes()}
        return nx.degree_centrality(undirected_G)

    def compute_betweenness_centrality(self) -> Dict[str, float]:
        """
        Computes Betweenness Centrality on the undirected structural view.
        Normalized.
        """
        undirected_G = self.get_undirected_view()
        if len(undirected_G) <= 1:
            return {n: 0.0 for n in undirected_G.nodes()}
        return nx.betweenness_centrality(undirected_G, weight=None)

    def compute_pagerank(self) -> Dict[str, float]:
        """
        Computes PageRank. 
        Uses the original graph (directed if passed as DiGraph) because influence flows directionally.
        """
        if len(self.graph) == 0:
            return {}
        try:
            return nx.pagerank(self.graph, weight=None)
        except (nx.PowerIterationFailedConvergence, ModuleNotFoundError, ImportError):
            return {n: 0.0 for n in self.graph.nodes()}

    def compute_eigenvector_centrality(self) -> Dict[str, float]:
        """
        Computes Eigenvector Centrality on the undirected view.
        """
        undirected_G = self.get_undirected_view()
        if len(undirected_G) <= 1:
            return {n: 0.0 for n in undirected_G.nodes()}
        try:
            return nx.eigenvector_centrality(undirected_G, max_iter=1000, tol=1e-06, weight=None)
        except (nx.PowerIterationFailedConvergence, ModuleNotFoundError, ImportError):
            return {n: 0.0 for n in undirected_G.nodes()}

    def compute_k_core(self) -> Dict[str, int]:
        """
        Computes K-Core decomposition on the undirected view.
        Returns the core number for each node.
        """
        undirected_G = self.get_undirected_view()
        # Remove self-loops before calculating k-core
        G_no_loops = undirected_G.copy()
        G_no_loops.remove_edges_from(nx.selfloop_edges(G_no_loops))
        return nx.core_number(G_no_loops)

    def compute_communities(self) -> Dict[str, Any]:
        """
        Detects topological communities using Louvain (if available) or Label Propagation.
        Returns algorithm name and community assignments.
        Uses undirected view.
        """
        undirected_G = self.get_undirected_view()
        assignments = {}
        
        if LOUVAIN_AVAILABLE:
            algorithm = "LOUVAIN"
            # seed=42 for determinism
            communities = list(louvain_communities(undirected_G, seed=42))
        else:
            algorithm = "LABEL_PROPAGATION"
            communities = list(label_propagation_communities(undirected_G))
            
        # Sort communities for deterministic IDs
        communities_sorted = sorted([list(c) for c in communities], key=lambda c: (-len(c), min(c) if c else ""))
        
        for idx, comp in enumerate(communities_sorted):
            comp_id = f"COMMUNITY_{idx+1}"
            for node in comp:
                assignments[node] = comp_id
                
        return {
            "algorithm": algorithm,
            "assignments": assignments
        }

    def compute_bridge_analysis(self) -> Dict[str, Any]:
        """
        Identifies structural bridges and articulation points.
        Uses undirected view.
        """
        undirected_G = self.get_undirected_view()
        
        # Articulation points
        articulation_points = list(nx.articulation_points(undirected_G))
        # Bridge edges
        bridges = list(nx.bridges(undirected_G))
        
        return {
            "articulation_points": articulation_points,
            "bridges": [{"source": u, "target": v} for u, v in bridges]
        }

    def find_bounded_shortest_path(self, source: str, target: str, max_hops: int = 5) -> Dict[str, Any]:
        """
        Finds the shortest path bounded by max_hops.
        Respects the directedness of the original graph if directed.
        """
        if source not in self.graph or target not in self.graph:
            return {"status": "error", "message": "Source or target not found in graph"}
            
        if source == target:
            return {"status": "error", "message": "Source and target are identical"}
            
        try:
            # We use undirected view if we want to trace relationships backwards too, 
            # but the contract implies "appropriate graph representation".
            # For investigative paths, often any direction is acceptable, so we use undirected for paths.
            undirected_G = self.get_undirected_view()
            path = nx.shortest_path(undirected_G, source=source, target=target)
            
            if len(path) - 1 > max_hops:
                return {"status": "error", "message": "Path exceeds maximum allowed hops"}
                
            path_rels = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                # Try to get edge data from original graph to capture properties/direction
                edge_data = self.graph.get_edge_data(u, v) or self.graph.get_edge_data(v, u)
                rel_type = edge_data.get("type", "UNKNOWN") if edge_data else "UNKNOWN"
                path_rels.append({"source": u, "target": v, "type": rel_type})
                
            return {
                "status": "success",
                "source": source,
                "target": target,
                "path_nodes": path,
                "path_relationships": path_rels,
                "path_length": len(path) - 1
            }
        except nx.NetworkXNoPath:
            return {"status": "error", "message": "No path exists between source and target"}

    def run_all_metrics(self) -> Dict[str, Any]:
        """
        Runs all node-level and graph-level structural metrics in Phase 1.
        """
        return {
            "components": self.get_components(),
            "degree_centrality": self.compute_degree_centrality(),
            "betweenness_centrality": self.compute_betweenness_centrality(),
            "pagerank": self.compute_pagerank(),
            "eigenvector_centrality": self.compute_eigenvector_centrality(),
            "k_core": self.compute_k_core(),
            "communities": self.compute_communities(),
            "bridges": self.compute_bridge_analysis()
        }
