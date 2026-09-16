import pytest
import uuid
import networkx as nx
from unittest.mock import MagicMock, patch

from backend.db.models.analytics import ModelRun, NetworkMetric
from backend.services.analysis_service import AnalysisService

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    # Ensure query returns mock objects where necessary
    run_mock = MagicMock(spec=ModelRun)
    run_mock.run_id = uuid.uuid4()
    run_mock.case_id = uuid.uuid4()
    run_mock.task_type = "SNA"
    
    query_mock = MagicMock()
    query_mock.filter.return_value.first.return_value = run_mock
    session.query.return_value = query_mock
    
    return session, run_mock

@patch("backend.graph.graph_extractor.GraphExtractor")
@pytest.mark.asyncio
async def test_async_analysis_worker(mock_extractor_class, mock_db_session):
    from apps.api.routers.evidence_analysis import _async_analysis_worker
    
    session, run_mock = mock_db_session
    mock_factory = MagicMock(return_value=session)
    
    # Setup mock graph
    G = nx.DiGraph()
    G.add_edge("E1", "E2", type="KNOWS")
    
    mock_extractor_inst = MagicMock()
    mock_extractor_inst.extract_case_graph.return_value = G
    mock_extractor_class.return_value = mock_extractor_inst
    
    # Run the worker
    await _async_analysis_worker(run_mock.run_id, run_mock.case_id, session_factory=lambda: session)
    
    # Verification
    assert run_mock.status == "SUCCESS"
    assert session.commit.called
    assert session.bulk_save_objects.called
    
    # Verify some metrics were saved
    call_args = session.bulk_save_objects.call_args[0][0]
    metric_types = [m.metric_type for m in call_args]
    
    assert "COMPONENT_COUNT" in metric_types
    assert "DEGREE_CENTRALITY" in metric_types
    assert "PAGERANK" in metric_types

@patch("backend.graph.graph_extractor.GraphExtractor")
@pytest.mark.asyncio
async def test_analysis_case_isolation(mock_extractor_class, mock_db_session):
    """
    Security regression test: Proves strict case isolation.
    Analysis for Case A must never extract or persist metrics for Case B.
    """
    from apps.api.routers.evidence_analysis import _async_analysis_worker
    
    session, run_mock = mock_db_session
    mock_factory = MagicMock(return_value=session)
    
    expected_case_id = run_mock.case_id
    
    G = nx.DiGraph()
    G.add_edge("E1", "E2", type="KNOWS")
    
    mock_extractor_inst = MagicMock()
    mock_extractor_inst.extract_case_graph.return_value = G
    mock_extractor_class.return_value = mock_extractor_inst
    
    await _async_analysis_worker(run_mock.run_id, expected_case_id, session_factory=lambda: session)
    
    # 1. Verify extractor was called precisely with expected_case_id
    mock_extractor_inst.extract_case_graph.assert_called_once_with(str(expected_case_id))
    
    # 2. Verify all persisted metrics strictly belong to expected_case_id
    assert session.bulk_save_objects.called
    call_args = session.bulk_save_objects.call_args[0][0]
    for metric in call_args:
        assert metric.case_id == expected_case_id, "CRITICAL SECURITY FAILURE: Metric persisted to wrong case"
