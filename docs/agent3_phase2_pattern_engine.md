# Agent 3 Phase 2: Deterministic Pattern & Motif Alert Engine

## Overview
This document outlines the architecture and implementation of the **Deterministic Pattern & Motif Alert Engine** (Agent 3 Phase 2) for the SIH26189 AI-Powered Criminal Network Analysis System.

The Pattern Engine operates as an offline analytical orchestrator designed to find specific structural and temporal subgraphs (motifs) within the investigation case data. It focuses on deterministic, reproducible alerting rather than probabilistic machine learning, ensuring that human investigators have explainable, evidence-backed leads.

## Architectural Principles
1. **Determinism:** All patterns use explicit thresholds (e.g., degree constraints, time windows). The engine does not rely on random sampling or non-deterministic thresholds.
2. **Explainability:** Alerts provide human-readable metadata, specifically listing contributing focal nodes, counterparties, and the source transaction/communication IDs.
3. **No Cross-Case Contamination:** The engine strictly enforces case boundaries. Graph traversals and SQL queries are rigidly bound by `case_id`.
4. **Non-Destructive Graph Interaction:** The engine reads evidence and writes to an isolated `alerts` table in PostgreSQL. It never overwrites or alters the original source nodes/edges.
5. **Idempotency:** Alerts are fingerprinted using a SHA256 hash of the `case_id`, `rule_id`, `contributing_entities`, and evaluation window. Running the engine multiple times on the same evidence yields the same alerts without duplicating records.
6. **Temporal Safety:** A centralized `temporal.py` validator handles timestamp constraints. Null, missing, or malformed timestamps trigger a `TemporalSafetyError`, yielding an `INSUFFICIENT_TEMPORAL_DATA` alert rather than silently skipping the pattern.

## Core Components
### `PatternEngine` (`agents/intelligence/pattern_engine.py`)
The orchestrator that loads the requested detectors and runs them against a specific `case_id`. It aggregates the generated `AlertCandidate` instances and uses the `AlertRepository` for deduplicated persistence.

### `BaseDetector` (`agents/intelligence/base_detector.py`)
An abstract base class enforcing the contract for all detectors. Detectors must implement the `detect()` method returning a list of `AlertCandidate` instances.

### `AlertRepository` (`backend/repositories/alert_repository.py`)
Handles persistent storage of generated alerts into the PostgreSQL System of Record. Implements `save_alerts_idempotent` utilizing SHA256 fingerprinting for robust deduplication.

### `TemporalSafety` (`agents/intelligence/temporal.py`)
Centralized time-validation logic. Provides `validate_timestamps` and `safe_time_difference_hours` to ensure that algorithms like Communication Bursts are not operating on corrupted timelines.

### `PatternThresholds` (`agents/intelligence/thresholds.py`)
A centralized configuration object (e.g., `FAN_OUT_MIN_DEGREE = 5`) allowing investigators to tune pattern sensitivity globally.

## Implemented Detectors
### 1. Transaction Cycles (`transaction_cycles.py`)
- **Objective:** Detect money laundering typologies where funds move through intermediate accounts and return to the original sender within a specific time window.
- **Methodology:** Time-aware Depth First Search (DFS) on the transaction graph, filtering out edges that violate temporal ordering or exceed `TX_CYCLE_MAX_WINDOW_HOURS`.
- **Alert:** `TRANSACTION_CYCLE`

### 2. Rapid Fan-In / Fan-Out (`fan_in_fan_out.py`)
- **Objective:** Detect nodes that suddenly disburse (Fan-Out) or aggregate (Fan-In) funds from many unique counterparties in a short period.
- **Methodology:** Sliding window approach over sorted transactions to find dense clusters exceeding `FAN_IN_MIN_DEGREE` or `FAN_OUT_MIN_DEGREE` within `FAN_WINDOW_HOURS`.
- **Alert:** `RAPID_FAN_OUT`, `RAPID_FAN_IN`

### 3. Communication Bursts (`communication_burst.py`)
- **Objective:** Detect anomalous spikes in communications immediately following a significant event (e.g., an ARREST event).
- **Methodology:** Baseline analysis over `COMM_BURST_BASELINE_WINDOW_HOURS`, comparing frequency with an incident window. A burst is declared if the frequency exceeds the baseline by `COMM_BURST_MULTIPLIER`.
- **Alert:** `COMMUNICATION_BURST`

### 4. Cross-Community Bridges (`cross_community_bridge.py`)
- **Objective:** Identify pivotal actors who act as the sole communicators between two otherwise distinct network communities.
- **Methodology:** Leverages `SNAEngine` for Louvain/Label Propagation community detection. Nodes with high betweenness centrality and connections spanning multiple communities are flagged.
- **Alert:** `CROSS_COMMUNITY_BRIDGE`

## Asynchronous Worker Integration
The `PatternEngine` is integrated into the system's Celery/Background task worker (`evidence_analysis.py`). When a pipeline task requests `PATTERN` analysis, the engine is triggered, making it entirely decoupled from the synchronous HTTP request-response cycle.
