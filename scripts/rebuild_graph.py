#!/usr/bin/env python3
"""
CLI Script for SIH26189 to forcefully rebuild the Neo4j analytical projection
from the authoritative PostgreSQL system of record.
"""

import argparse
import logging
import os
import sys
from uuid import UUID

# Ensure project root is in sys.path for standalone script execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.session import SessionLocal
from backend.services.graph_projection import GraphProjectionService
from backend.repositories.neo4j_repository import Neo4jRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rebuild_graph")


def main():
    parser = argparse.ArgumentParser(description="Force rebuild Neo4j graph projection from PostgreSQL.")
    parser.add_argument("--case-id", type=str, help="UUID of the case to rebuild.", required=False)
    parser.add_argument("--all", action="store_true", help="Rebuild all cases.")
    
    args = parser.parse_args()

    if not args.case_id and not args.all:
        parser.error("Must specify either --case-id <UUID> or --all.")

    if args.case_id and args.all:
        parser.error("Cannot specify both --case-id and --all.")

    # Step 1: Ensure constraints exist
    repo = Neo4jRepository()
    repo.initialize_constraints()
    
    db = SessionLocal()
    service = GraphProjectionService(db=db)

    try:
        if args.case_id:
            try:
                case_uuid = UUID(args.case_id)
            except ValueError:
                parser.error("Invalid UUID format for --case-id")
                
            logger.info(f"Rebuilding graph for single case: {case_uuid}")
            result = service.rebuild_case_graph(case_uuid)
            logger.info(f"Rebuild complete. Result: {result}")
        elif args.all:
            from backend.db.models.identity import Case
            cases = db.query(Case).all()
            logger.info(f"Rebuilding graph for all {len(cases)} cases.")
            for c in cases:
                logger.info(f"Rebuilding case: {c.case_id}")
                result = service.rebuild_case_graph(c.case_id)
                logger.info(f"Case {c.case_id} rebuild result: {result}")
    except Exception as e:
        logger.error(f"Failed to rebuild graph: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
