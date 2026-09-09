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
- **Primary OCR Engine:** **PaddleOCR** (primary document OCR for document preprocessing and image text extraction).
- **Planned Technology Stack:**
  - *OCR Engine:* **PaddleOCR**
  - *NER Model:* **IndicNER**
  - *Legal Domain LLM:* **InLegalBERT**
  - *Embedding Models:* **multilingual-E5-large-instruct / IndicSBERT** (for document and text embeddings)
  - *Generative Extraction & Explanation LLM:* **Qwen3-4B-Instruct-2507** (for structured extraction and explanation generation)
  - *Entity Resolution Engine:* **Dedupe + deterministic rules + embeddings**
  - *Graph Learning Engine:* **PyTorch Geometric (PyG) + GATv2**
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
- **Entity Resolution Pipeline [PLANNED ARCHITECTURE]:** Utilizes deterministic rules first (e.g., exact matches of phone numbers, account identifiers, vehicle plates), followed by fuzzy name similarity (Jaro-Winkler, Levenshtein) and embedding vector similarity (Dedupe framework). Ambiguous candidate matches below a configurable confidence threshold (default `< 0.85`, subject to empirical calibration on validation sets) are quarantined and routed to a supervisor's `REVIEW_REQUIRED` queue. Case-scoped resolution and provenance preservation are strictly enforced.
- **Belief Engine [PLANNED ARCHITECTURE / VALIDATION REQUIRED]:** Subjective Logic operators combine belief metrics across multi-source evidence. Implemented as part of the planned architecture, requiring dedicated mathematical validation testing before production deployment.

#### 5.4 Agent 3 (Network Intelligence & Prediction Engine) [CURRENT/FINAL]

This service contains four distinct pipelines:

##### A. Social Network Analysis (SNA)

- **Processing Order:** Connected Components -> Centrality Calculations (Degree, Betweenness, Eigenvector/PageRank) -> Community Detection (Louvain/Label Propagation) -> Path & Bridge detection.
- **Research Grounding (Community Detection):** Community detection uses explainable classical SNA (Louvain / Label Propagation) as the primary operational path. Research literature (*CrimeGNN*) provides theoretical support for GNN-derived community representations in criminal networks; CrimeGNN is maintained as an optional experimental benchmark, not a mandatory replacement for explainable SNA.
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
- **Research Grounding:** Informed by criminal-network link-prediction research (*CrimeGraphNet*). CrimeGraphNet provides domain-specific support for graph neural networks in criminal network link prediction; its formulation informs our feature design and evaluation strategy, while SIH26189 uses GATv2 as the selected graph architecture because architecture choice remains an empirical engineering decision. GATv2 is a planned/core research capability whose final production role is subject to empirical validation against baselines.
- **Node Feature Matrix:** 
  - Entity Type (One-hot encoded)
  - Centrality Metrics (SNA Degree, Betweenness, PageRank)
  - Temporal Activity Profile & Frequency Indices (combining structural and temporal signals, inspired by spatial/temporal graph representation literature)
  - Geographical / Spatial & Jurisdictional Attributes (Normalized coordinates and jurisdictional boundaries)
  - Evidence Statistics & Degree Metrics
  - *Prohibited Features:* Raw IMSI, account sequences, and phone values are completely rejected.
- **Edge Feature Matrix (Side Information):** 
  - Relationship Classification Type (One-hot encoded)
  - Observation Frequency
  - Recency Indicators (Time decay values)
  - Evidence Logic Scores (`belief`, `disbelief`, `uncertainty`)
  - Projected Evidence Confidence Metrics
- **Imbalance & Loss Handling:** Utilizes weighted loss functions and negative sampling strategies suited for imbalanced criminal network link prediction (*CrimeGraphNet*).
- **Benchmark Baselines:** GATv2 results must be validated against classical graph heuristics (*Common Neighbors*, *Jaccard Index*, *Adamic-Adar*, *Preferential Attachment*) and a simple Multi-Layer Perceptron (MLP) baseline.
- **Leakage Checks:** Chronological partitioning of train, validation, and test datasets is required (ensuring the model does not predict past transactions using future transactional context).

##### D. Investigative-Priority Ranking

- **Role:** Evaluates entity priority using a weighted function of SNA values, alert motifs, GATv2 embeddings, and temporal recency metrics.
- **Language Check:** Priority rankings must never be called "Guilt Ratios" or "Crime Probabilities." Outputs are strictly labeled as "Priority Rankings" and "Investigative Leads."

##### E. AI Explanation Panel

- **Requirement:** Every AI prediction must generate an explanation containing: the analytical reasoning, versioned model indicators, contributing node features, confidence semantics, and known model limitations.
- **Fallback Strategy:** If the model explanation engine fails or is offline, the interface must render a pre-defined, deterministic template explanation.

---
