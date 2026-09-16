import json
import hashlib
from typing import Dict, Any, Tuple
import networkx as nx

try:
    import torch
    from torch_geometric.data import Data
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False


class Agent3DatasetAdapter:
    """
    Adapter to parse raw JSON datasets and prepare them for:
    1. Postgres Metadata Insertion
    2. Neo4j Idempotent Graph Projection
    3. PyTorch Geometric / NetworkX for Analytics
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._parsed_data = None
        self._sha256 = None
        self._load()

    def _load(self):
        with open(self.filepath, 'rb') as f:
            raw_data = f.read()
            self._sha256 = hashlib.sha256(raw_data).hexdigest()
            self._parsed_data = json.loads(raw_data)

    @property
    def checksum(self) -> str:
        return self._sha256

    @property
    def metadata(self) -> Dict[str, Any]:
        graph = self._parsed_data.get("graph", {})
        nodes = self._parsed_data.get("nodes", [])
        links = self._parsed_data.get("links", [])
        return {
            "name": graph.get("name", "Unknown Dataset"),
            "version": str(graph.get("version", "1.0")),
            "source_file": self.filepath,
            "checksum": self.checksum,
            "node_count": len(nodes),
            "edge_count": len(links),
            "schema_version": "1.0"
        }

    @property
    def raw_data(self) -> Dict[str, Any]:
        return self._parsed_data

    def to_networkx(self) -> nx.Graph:
        """
        Converts the dataset to a NetworkX Graph or DiGraph.
        """
        is_directed = self._parsed_data.get("directed", False)
        is_multigraph = self._parsed_data.get("multigraph", False)
        
        if is_multigraph:
            G = nx.MultiDiGraph() if is_directed else nx.MultiGraph()
        else:
            G = nx.DiGraph() if is_directed else nx.Graph()

        # Add Nodes
        for node in self._parsed_data.get("nodes", []):
            node_id = node.get("id")
            if node_id is None:
                continue
            attrs = {k: v for k, v in node.items() if k != "id"}
            G.add_node(node_id, **attrs)

        # Add Edges
        for link in self._parsed_data.get("links", []):
            source = link.get("source")
            target = link.get("target")
            if source is None or target is None:
                continue
            attrs = {k: v for k, v in link.items() if k not in ("source", "target")}
            G.add_edge(source, target, **attrs)

        return G

    def to_pyg(self) -> 'Data':
        """
        Converts the dataset to a PyTorch Geometric Data object.
        Extracts embedding keys into x tensors if they exist.
        """
        if not PYG_AVAILABLE:
            raise ImportError("PyTorch Geometric is not installed.")

        nodes = self._parsed_data.get("nodes", [])
        links = self._parsed_data.get("links", [])
        
        # Determine node ID mapping (PyG requires contiguous integer IDs starting at 0)
        id_map = {}
        for i, node in enumerate(nodes):
            id_map[node.get("id")] = i

        # Extract node features (embeddings)
        x_list = []
        for node in nodes:
            # We look for keys starting with 'emb_'
            emb_keys = [k for k in node.keys() if k.startswith("emb_")]
            emb_vector = []
            for k in sorted(emb_keys):
                val = node[k]
                if isinstance(val, str) and val.strip().startswith("["):
                    import json
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                if isinstance(val, (list, tuple)):
                    emb_vector.extend([float(v) for v in val if isinstance(v, (int, float))])
                elif isinstance(val, (int, float)):
                    emb_vector.append(float(val))
            x_list.append(emb_vector)
        
        max_len = max((len(v) for v in x_list), default=0)
        if max_len > 0:
            for v in x_list:
                v.extend([0.0] * (max_len - len(v)))
            x_tensor = torch.tensor(x_list, dtype=torch.float)
        else:
            x_tensor = None

        # Build edge index
        edge_sources = []
        edge_targets = []
        edge_weights = []

        for link in links:
            source = link.get("source")
            target = link.get("target")
            if source in id_map and target in id_map:
                edge_sources.append(id_map[source])
                edge_targets.append(id_map[target])
                edge_weights.append(link.get("weight", 1.0))
        
        edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)
        edge_attr = torch.tensor(edge_weights, dtype=torch.float)

        data = Data(x=x_tensor, edge_index=edge_index, edge_attr=edge_attr)
        
        # Optional: Add original IDs for mapping back
        data.node_ids = [node.get("id") for node in nodes]
        
        return data
