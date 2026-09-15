import pytest
import os
import torch
import networkx as nx
from agents.intelligence.dataset_adapter import Agent3DatasetAdapter

OFFENDER_DATASET_PATH = "data/agent3/raw/israel_lea_inp_burglary_offender_id_network.json"
CRIME_DATASET_PATH = "data/agent3/raw/israel_lea_inp_burglary_v2_crime_id_network.json"

@pytest.fixture
def offender_adapter():
    if not os.path.exists(OFFENDER_DATASET_PATH):
        pytest.skip(f"Dataset not found: {OFFENDER_DATASET_PATH}")
    return Agent3DatasetAdapter(OFFENDER_DATASET_PATH)

@pytest.fixture
def crime_adapter():
    if not os.path.exists(CRIME_DATASET_PATH):
        pytest.skip(f"Dataset not found: {CRIME_DATASET_PATH}")
    return Agent3DatasetAdapter(CRIME_DATASET_PATH)

def test_metadata_extraction(offender_adapter):
    meta = offender_adapter.metadata
    assert meta["name"] == "Israel Burglary - Offender Network"
    assert meta["node_count"] == 17237
    assert meta["edge_count"] == 21302
    assert "checksum" in meta

def test_networkx_conversion_offender(offender_adapter):
    G = offender_adapter.to_networkx()
    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() == 17237
    assert G.number_of_edges() == 21302

def test_networkx_conversion_crime(crime_adapter):
    G = crime_adapter.to_networkx()
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 23385
    assert G.number_of_edges() == 42607

def test_pyg_conversion_crime(crime_adapter):
    data = crime_adapter.to_pyg()
    assert data.x is not None
    assert isinstance(data.x, torch.Tensor)
    assert data.x.shape[0] == 23385
    assert data.x.shape[1] == 1386  # Check embedding dim
    assert data.edge_index is not None
    assert data.edge_index.shape[1] == 42607
