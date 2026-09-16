import asyncio
import logging
import uuid
import argparse
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import settings
from backend.repositories.postgres_session import engine, async_session_maker
from backend.repositories.neo4j_driver import driver
from backend.db.models.analytics import Agent3Dataset
from agents.intelligence.dataset_adapter import Agent3DatasetAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A deterministic namespace UUID for Agent 3 datasets
AGENT3_NAMESPACE = uuid.UUID("11111111-2222-3333-4444-555555555555")

async def upsert_postgres_metadata(session: AsyncSession, adapter: Agent3DatasetAdapter) -> uuid.UUID:
    """
    Upserts dataset metadata to PostgreSQL and returns the dataset UUID.
    """
    meta = adapter.metadata
    dataset_name = meta["name"]
    # Deterministic UUID for the dataset based on its name
    dataset_id = uuid.uuid5(AGENT3_NAMESPACE, dataset_name)
    
    # Query if exists
    from sqlalchemy import select
    result = await session.execute(select(Agent3Dataset).where(Agent3Dataset.dataset_id == dataset_id))
    record = result.scalars().first()
    
    if not record:
        record = Agent3Dataset(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            version=meta["version"],
            source_file=meta["source_file"],
            checksum=meta["checksum"],
            node_count=meta["node_count"],
            edge_count=meta["edge_count"],
            schema_version=meta["schema_version"],
            imported_at=datetime.now(timezone.utc)
        )
        session.add(record)
        logger.info(f"Inserting new metadata for {dataset_name} ({dataset_id})")
    else:
        record.checksum = meta["checksum"]
        record.node_count = meta["node_count"]
        record.edge_count = meta["edge_count"]
        logger.info(f"Updating metadata for {dataset_name} ({dataset_id})")
    
    await session.commit()
    return dataset_id

def upload_to_neo4j(adapter: Agent3DatasetAdapter, dataset_id: uuid.UUID):
    """
    Idempotent projection of the dataset to Neo4j.
    """
    raw = adapter.raw_data
    nodes = raw.get("nodes", [])
    links = raw.get("links", [])
    dataset_name = raw.get("graph", {}).get("name", "")
    
    is_crime = "crime" in dataset_name.lower()
    node_label = "Crime" if is_crime else "Offender"
    
    # Prepare parameters for batched UNWIND
    node_params = []
    for n in nodes:
        node_id_str = str(n.get("id"))
        n_uuid = str(uuid.uuid5(dataset_id, node_id_str))
        props = {k: v for k, v in n.items() if k != "id"}
        node_params.append({
            "entity_id": n_uuid,
            "original_id": node_id_str,
            "dataset_id": str(dataset_id),
            **props
        })
        
    edge_params = []
    for e in links:
        source_id = str(e.get("source"))
        target_id = str(e.get("target"))
        s_uuid = str(uuid.uuid5(dataset_id, source_id))
        t_uuid = str(uuid.uuid5(dataset_id, target_id))
        edge_uuid = str(uuid.uuid5(dataset_id, f"{s_uuid}_{t_uuid}"))
        props = {k: v for k, v in e.items() if k not in ("source", "target")}
        edge_params.append({
            "relationship_id": edge_uuid,
            "source": s_uuid,
            "target": t_uuid,
            "dataset_id": str(dataset_id),
            **props
        })

    cypher_node = f"""
    UNWIND $batch AS row
    MERGE (n:Entity:{node_label} {{entity_id: row.entity_id}})
    ON CREATE SET n += row, n.created_at = datetime()
    ON MATCH SET n += row, n.updated_at = datetime()
    """

    cypher_edge = """
    UNWIND $batch AS row
    MATCH (s:Entity {entity_id: row.source})
    MATCH (t:Entity {entity_id: row.target})
    MERGE (s)-[r:RELATION {relationship_id: row.relationship_id}]->(t)
    ON CREATE SET r += row, r.created_at = datetime()
    ON MATCH SET r += row, r.updated_at = datetime()
    """

    with driver.session(database=settings.NEO4J_DATABASE) as session:
        # Check GDS version
        try:
            gds_result = session.run("RETURN gds.version() AS v")
            logger.info(f"Neo4j GDS Version: {gds_result.single()['v']}")
        except Exception as e:
            logger.warning(f"Neo4j GDS plugin might not be available: {e}")
            
        # Batch upload nodes (batch size 1000)
        batch_size = 1000
        logger.info(f"Uploading {len(node_params)} nodes to Neo4j...")
        for i in range(0, len(node_params), batch_size):
            batch = node_params[i:i + batch_size]
            session.run(cypher_node, batch=batch)
            
        # Batch upload edges
        logger.info(f"Uploading {len(edge_params)} edges to Neo4j...")
        for i in range(0, len(edge_params), batch_size):
            batch = edge_params[i:i + batch_size]
            session.run(cypher_edge, batch=batch)

async def main():
    parser = argparse.ArgumentParser(description="Ingest Agent 3 Datasets")
    parser.add_argument('--files', nargs='+', required=True, help="Paths to raw JSON datasets")
    args = parser.parse_args()
    
    # 1. Process files
    for filepath in args.files:
        logger.info(f"Processing dataset: {filepath}")
        adapter = Agent3DatasetAdapter(filepath)
        
        # 2. Upsert Metadata
        async with async_session_maker() as session:
            dataset_id = await upsert_postgres_metadata(session, adapter)
            
        # 3. Neo4j Upload
        try:
            upload_to_neo4j(adapter, dataset_id)
        except Exception as e:
            logger.error(f"Failed to upload to Neo4j. Check database connectivity. Error: {e}")
            
    await engine.dispose()
    driver.close()

if __name__ == "__main__":
    asyncio.run(main())
