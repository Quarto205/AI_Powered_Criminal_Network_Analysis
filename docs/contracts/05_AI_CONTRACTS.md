# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 5: AI & MACHINE LEARNING CONTRACTS

AI-powered decision-support operations are split across independent pipelines, which are integrated via versioned data contracts.

```
+------------------+     +-----------------------+     +-------------------------+
|    OCR Service   | --> | Agent 1 (NLP Parser)  | --> | Agent 2 (Graph Builder) |
| (Tesseract/Local)|     | (Gemini/NER Provider) |     |  (Relational Database)  |
+------------------+     +-----------------------+     +-------------------------+
                                                                    |
                                                                    v
+------------------+     +-----------------------+     +-------------------------+
|   GATv2 Model    | <-- | Agent 3 (Network Eng) | <-- |    Neo4j Graph Store    |
| (PyTorch/PyG ML) |     | (Centrality/Motifs)   |     |    (Graph Projection)   |
+------------------+     +-----------------------+     +-------------------------+

```

#### 5.1 OCR Processing [CURRENT/FINAL]

- **Status:** Preprocessor service, not an agent loop.
- **Provider:** Local engine or OCR provider. [OCR/model provider choice UNCERTAIN].
- **Safety Restriction:** PDF parsing errors must fail cleanly and quarantine the document, preventing malformed characters from entering the text parsing pipelines.

#### 5.2 Agent 1 (Intelligence Extraction Parser) [CURRENT/FINAL]

- **Role:** Extracts structured semantic units from raw untrusted text documents.
- **Input Schema:** Text chunks, chunk identifiers, character metadata.
- **Output Schema (Pydantic/JSON Contract):** 
  ```
  {
    "extraction_job_id": "UUID",
    "extracted_entities": [
      {
        "temp_id": "string",
        "entity_type": "PERSON | PHONE | VEHICLE | BANK_ACCOUNT",
        "extracted_text": "string",
        "character_start": 0,
        "character_end": 0
      }
    ],
    "extracted_relationships": [
      {
        "source_temp_id": "string",
        "target_temp_id": "string",
        "type": "string",
        "context_span": "string",
        "confidence_score": 0.0
      }
    ]
  }

  ```
- **Safety Limits:** Raw document text must be treated as untrusted to mitigate prompt-injection attacks. Model execution cannot trigger external tools or call runtime code.

#### 5.3 Agent 2 (Evidence & Graph Maintenance) [CURRENT/FINAL]

- **Role:** Performs entity resolution, alias linking, validation checks, and database normalization.
- **Entity Resolution Pipeline [PROVISIONAL]:** Utilizes deterministic rules first (e.g., exact matches of phone numbers, account identifiers, vehicle plates), then similarity metrics (Jaro-Winkler, Levenshtein name heuristics). Low-confidence matching sets (e.g., `< 0.85`) are quarantined and routed to a supervisor's `REVIEW_REQUIRED` queue.
- **Belief Engine [NEEDS VALIDATION]:** Subjective Logic operators combine belief metrics.

#### 5.4 Agent 3 (Network Intelligence & Prediction Engine) [CURRENT/FINAL]

This service contains four distinct pipelines:

##### A. Social Network Analysis (SNA)

- **Processing Order:** Connected Components -> Centrality Calculations (Degree, Betweenness, Eigenvector/PageRank) -> Community Detection (Louvain/Label Propagation) -> Path & Bridge detection.
- **Directed vs. Undirected Treatment:** Directed attributes are computed strictly for communication paths and financial chains; kinship or general contacts use undirected networks.
- **Calculation Runtime:** Executed using Neo4j graph data science (GDS) libraries or NetworkX. Calculated attributes are cached separately in a PostgreSQL analysis log, rather than modifying raw node properties.

##### B. Deterministic Motif Alerts

- **Role:** Rules engine scanning timestamped transactions.
- **Rules Definitions:** 
  1. *Transaction Cycles:* `A -> B -> C -> A` financial routes within short temporal windows.
  2. *Communication Bursts:* High-frequency call logs occurring around incident times.
  3. *Rapid Fan-out / Fan-in:* Single accounts distributing money to multiple recipients within minutes.
  4. *Bridge Nodes:* Accounts linking distinct local communities.
- **Requirement:** Incomplete transaction dates or times must generate an "Insufficient Temporal Data" flag, rather than a false warning.

##### C. Supervised GATv2 GNN Model

- **Task Scope:** Strictly link-prediction and association scoring. [GATv2 Kingpin Detection is REJECTED].
- **Node Feature Matrix:** 
  - Entity Type (One-hot encoded)
  - Centrality Metrics (SNA Degree, Betweenness, PageRank)
  - Temporal Activity Profile (Frequency indices)
  - Geographical Coordinates (Normalized coordinates grid)
  - *Prohibited Features:* Raw IMSI, account sequences, and phone values are completely rejected.
- **Edge Feature Matrix:** 
  - Relationship Classification Type (One-hot encoded)
  - Observation Frequency
  - Recency Indicators (Time decay values)
  - Evidence Logic Scores (`belief`, `disbelief`, `uncertainty`)
- **Benchmark Baselines:** GATv2 results must be validated against classical graph heuristics (*Common Neighbors*, *Jaccard Index*, *Adamic-Adar*, *Preferential Attachment*) and a simple Multi-Layer Perceptron (MLP) baseline.
- **Leakage Checks:** Chronological partitioning of train, validation, and test datasets is required (ensuring the model does not predict past transactions using future transactional context).

##### D. Investigative-Priority Ranking

- **Role:** Evaluates entity priority using a weighted function of SNA values, alert motifs, GATv2 embeddings, and temporal recency metrics.
- **Language Check:** Priority rankings must never be called "Guilt Ratios" or "Crime Probabilities." Outputs are strictly labeled as "Priority Rankings" and "Investigative Leads."

##### E. AI Explanation Panel

- **Requirement:** Every AI prediction must generate an explanation containing: the analytical reasoning, versioned model indicators, contributing node features, confidence semantics, and known model limitations.
- **Fallback Strategy:** If the model explanation engine fails or is offline, the interface must render a pre-defined, deterministic template explanation.

---
