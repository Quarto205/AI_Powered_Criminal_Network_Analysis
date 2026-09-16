# Agent 3 Phase 3: Link Prediction ML Pipeline

## Overview
This document outlines the design and implementation of the Phase 3 Link Prediction Machine Learning Pipeline for the AI-Powered Criminal Network Analysis System.
The objective is to identify missing or latent associations between entities based on existing structural and temporal network data.

## Architectural Principles
1. **Deterministic Execution**: The entire pipeline (DeepWalk, PyTorch GATv2 training, temporal splits) uses fixed random seeds and strict chronological sorting.
2. **Strict Isolation**: 
   - Feature engineering completely excludes raw identifiers (e.g. `phone_number`, `imsi`).
   - Edges are sorted chronologically. Training graphs explicitly mask any edge occurring after the cutoff time to prevent temporal leakage.
3. **Neo4j 2-Hop Candidate Generation**: To avoid O(N^2) pairwise explosion, candidate edges are generated directly within Neo4j using bounded 2-hop traversals enforcing semantic constraints (e.g., `PERSON -> [ANY] -> PERSON` expecting `ASSOCIATED_WITH`).
4. **Environment Safety**: A deterministic NetworkX-based DeepWalk algorithm was explicitly developed to substitute PyG Node2Vec, avoiding native C++ sparse compilation problems on Windows deployments.

## Components

### 1. `ml.preprocessing.candidate_pairs.CandidateGenerator`
Constructs parameterized Cypher queries running on the Neo4j instance to retrieve plausible non-existent pairs bounded by a maximum hop distance of 2. 

### 2. `ml.preprocessing.temporal_split.TemporalSplitter`
Sorts graph edges based on the true `created_at` timestamp. Masks out edges falling in the test percentage (e.g., 20%) to create a strictly past-observed training graph, solving temporal data leakage.

### 3. `ml.preprocessing.feature_builder.FeatureBuilder`
Generates PyTorch Geometric-compatible Node (`x`) and Edge (`edge_attr`) tensors. Features explicitly merged include:
- Extracted SNA Metrics (Phase 1)
- DeepWalk Structural Embeddings
- Entity Type One-Hot vectors
- Temporal proximity (e.g., age of node/edge decay).

### 4. `ml.models.classical_baselines.ClassicalBaselines`
Calculates NetworkX baseline heuristics for candidate pairs, storing Common Neighbors, Jaccard Index, Preferential Attachment, Adamic-Adar, and Resource Allocation for comparative evaluation against GATv2.

### 5. `ml.models.gatv2.GATv2LinkPredictor`
The PyTorch Graph Attention Network v2. Encodes nodes using the attention mechanism over structural neighborhoods and decodes candidate pairs using a fully connected layer over the concatenated element-wise product and absolute difference of the embeddings.

### 6. Persistence
Predictions generated with high confidence are stored in the PostgreSQL System of Record in the `predictions` table, carrying `status="INFERRED"`. The system enforces that inferred edges NEVER overwrite source-backed structural facts.
