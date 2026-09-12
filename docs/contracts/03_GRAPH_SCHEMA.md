# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 3: NEO4J ANALYTICAL GRAPH SCHEMA [CURRENT/FINAL]

The Neo4j database is a pure, rebuildable projection of canonical evidence records stored in PostgreSQL.

```
                    [Person] ------------( OWNS )-------------> [Phone]
                       |                                           |
                 ( ACCUSED_IN )                            ( COMMUNICATED_WITH )
                       |                                           |
                       v                                           v
                   [Offense]                                    [Phone]
                       ^                                           |
                       |                                      ( USED_BY )
                 ( HAS_INCIDENT )                                  |
                       |                                           v
                       |                                       [Person]
                       |                                           |
                   [Location] <----------( LOCATED_AT )------------|

```

#### 3.1 Node Labels & Properties

- **Person:** `entity_id` (UUID), `display_name` (string), `status` (string), `alias_count` (integer)
- **Phone:** `entity_id` (UUID), `masked_identifier` (string)
- **BankAccount:** `entity_id` (UUID), `masked_identifier` (string), `provider` (string)
- **Vehicle:** `entity_id` (UUID), `masked_plate` (string), `type` (string)
- **Organization:** `entity_id` (UUID), `name` (string), `type` (string)
- **Location:** `entity_id` (UUID), `normalized_name` (string), `geography` (WKT Polygon/Point string)
- **Case:** `case_id` (UUID), `case_code` (string)
- **Evidence:** `evidence_id` (UUID), `source_type` (string, e.g., 'FIR', 'CDR\_CSV')
- **Offense:** `offense_id` (UUID), `category` (string), `code` (string)

#### 3.2 Relationship Types & Directions

- `(:Person)-[:ACCUSED_IN]->(:Offense)`
- `(:Person)-[:KNOWS]->(:Person)`
- `(:Person)-[:CONTACTED]->(:Person)`
- `(:Person)-[:LOCATED_AT]->(:Location)`
- `(:Person)-[:OWNS]->(:BankAccount|:Phone|:Vehicle|:Organization)`
- `(:Phone)-[:USED_BY]->(:Person)`
- `(:Phone)-[:COMMUNICATED_WITH]->(:Phone)`
- `(:Phone)-[:PINGED_TOWER]->(:Location)`
- `(:BankAccount)-[:TRANSFERRED_TO]->(:BankAccount)`
- `(:BankAccount)-[:OWNED_BY]->(:Person)`
- `(:Vehicle)-[:REGISTERED_TO]->(:Person|:Organization)`
- `(:Vehicle)-[:SCANNED_AT]->(:Location)`
- `(:Organization)-[:AFFILIATED_WITH]->(:Organization|:Person)`
- `(:Case)-[:CONTAINS]->(any node within the case scope)`
- `(:Evidence)-[:SUPPORTS|:REFUTES]->(any relationship or node target)`

#### 3.3 Relationship Evidence Properties

To prevent structural confusion, relationship lines are cleanly divided into two types:

##### Factual Evidence Edges

Every relationship that is constructed from verified case evidence holds these properties:

- `relationship_id` (UUID)
- `status` (string: `OBSERVED`, `CORROBORATED`, `CONFIRMED`, `REJECTED`)
- `source_ref_count` (integer)
- `relationship_confidence` (float)
- `confidence_type` (string)
- `belief` (float) - *Only active if Subjective Logic is validated.*
- `disbelief` (float) - *Only active if Subjective Logic is validated.*
- `uncertainty` (float) - *Only active if Subjective Logic is validated.*
- `observed_at` (datetime string)
- `created_at` (datetime string)
- `source_system` (string)
- `evidence_ids` (array of strings)

##### AI-Inferred Link Predictions

Edges predicted by supervised machine learning models (GATv2) are separate relationship classes or styled as prediction links containing:

- `prediction_id` (UUID)
- `model_run_id` (UUID)
- `score` (float `0.0 - 1.0`)
- `calibration_status` (string)
- `expiry_status` (string)
- `review_status` (string: `NEW`, `REVIEWED`, `CONFIRMED`, `REJECTED`)

#### 3.4 Projection & Reconstruction Invariant

- **Idempotency Invariant:** Writes to Neo4j must use `MERGE` actions based on stable application UUIDs. Global destructive resets (`MATCH (n) DETACH DELETE n`) are strictly forbidden inside standard workflows.
- **The Projection Rule:** Neo4j stores no authoritative application metadata. If the Neo4j container is corrupted or cleared, running the PostgreSQL database sync task must completely reconstruct the analytical graph layout without loss of investigative context.

---
