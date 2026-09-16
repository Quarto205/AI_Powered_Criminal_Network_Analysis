# Research Knowledge Base — SIH26189

**Project:** SIH26189 — AI-Powered Criminal Network Analysis System  
**Namespace:** `criminal-network-analysis`  
**Status:** Active Persistent Research Knowledge Base  
**Authority:** Supporting Research Knowledge (Research ≠ Project Requirement)  

---

## Document Overview & Conceptual Boundaries

This knowledge base documents the theoretical foundations, algorithmic mechanics, baselines, evaluation protocols, and project relevance of three external academic research papers reviewed for SIH26189:

1. **Paper 1:** *CrimeGraphNet: Link Prediction in Criminal Networks with Graph Convolutional Networks* (arXiv:2311.18543v1, 2023)
2. **Paper 2:** *CrimeGNN: Harnessing the Power of Graph Neural Networks for Community Detection in Criminal Networks* (arXiv:2311.17479v1, 2023)
3. **Paper 3:** *Graph Representation Learning for Street-Level Crime Prediction* (ISPRS Int. J. Geo-Inf. 2024, 13, 229)

### Non-Negotiable Research Boundary & Classification

In accordance with [`.agents/rules/core-project-rules.md`](file:///d:/AI-criminal-Network/.agents/rules/core-project-rules.md) and [`Useful/rules.md`](file:///d:/AI-criminal-Network/Useful/rules.md):
- **RESEARCH SOURCES ARE NOT PRODUCT REQUIREMENTS.**
- All extracted concepts are strictly classified into:
  - **`[RESEARCH FACT]`**: Empirically reported observation or design within the published paper.
  - **`[RESEARCH INSPIRATION]`**: Transferable technique or formulation relevant to SIH26189 experimentation.
  - **`[PROJECT DECISION]`**: Confirmed SIH26189 architectural decision already governed by canonical specs.
  - **`[NOT ADOPTED / OUT OF SCOPE]`**: Conceptual element from paper explicitly rejected or excluded from product scope.
  - **`[REQUIRES VALIDATION]`**: Promising concept requiring experimental testing on Indian/synthetic benchmarks before any adoption.
- **Paper reported benchmark figures belong solely to the cited papers.** They must never be represented as SIH26189 system performance.

---

## 1. Paper 1 — CrimeGraphNet

### Citation & Identity
- **Title:** *CrimeGraphNet: Link Prediction in Criminal Networks with Graph Convolutional Networks*
- **Author:** Chen Yang
- **Affiliation:** Shanghai Business School
- **Source Identifier:** arXiv:2311.18543v1 [cs.SI] (30 Nov 2023)
- **Local Artifact:** [`2311.18543v1.pdf`](file:///d:/AI-criminal-Network/2311.18543v1.pdf)

### Problem Definition `[RESEARCH FACT]`
- Targets link prediction in criminal networks: forecasting unobserved, missing, or future relationships between criminal entities.
- Addresses unique domain difficulties:
  - **Covertness:** Relationships and communications in criminal syndicates are intentionally hidden or obfuscated.
  - **Sparsity & Class Imbalance:** Verified criminal ties constitute a minute fraction of all possible node pairings ($|E| \ll |V| \times |V|$).
  - **Scarcity of Ground-Truth Labels:** Limited verified operational data available for supervised training.

### Graph Formulation `[RESEARCH FACT]`
- **Graph Representation:** $G = (V, E)$, where $V$ represents criminal entities (individuals, organizations) and $E$ represents relationships or interactions.
- **Adjacency Matrix:** $A \in \mathbb{R}^{n \times n}$, where $n = |V|$, with $A_{ij} = 1$ if an edge exists between node $i$ and node $j$, and $A_{ij} = 0$ otherwise.
- **Node Feature Matrix:** $X \in \mathbb{R}^{n \times d}$, where $d$ is the number of node features, and $X_{ik}$ represents the $k$-th attribute of node $i$.
- **Node Embeddings:** $H \in \mathbb{R}^{n \times p}$ learned by the GCN, where $p$ is embedding dimensionality.
- **Link Prediction Function:** $f: V \times V \rightarrow [0, 1]$, defined as:
  $$f(i, j) = \sigma(H_i^T H_j)$$
  where $\sigma$ is the sigmoid activation function producing an association probability score.

### Method & Mechanics `[RESEARCH FACT]`
- **GCN Layer Convolution:** Uses spectral graph convolution with renormalized adjacency:
  $$H^{(l+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)}\right)$$
  where $\tilde{A} = A + I_n$ (adjacency with added self-loops), $\tilde{D}_{ii} = \sum_j \tilde{A}_{ij}$, and $W^{(l)}$ is the layer weight parameter.
- **Handling Class Imbalance:** Employs a weighted binary cross-entropy loss based on inverse class frequencies to penalize false negatives heavily:
  $$\text{Loss} = -\frac{1}{N} \sum_{i=1}^{N} \left[ w_1 y_i \log(\hat{y}_i) + w_0 (1 - y_i) \log(1 - \hat{y}_i) \right]$$
- **Side Information Fusion:** Concatenates exogenous node attributes and derived network metrics (degree, centrality) with baseline features prior to message passing.

### Architecture & Training `[RESEARCH FACT]`
- **Model Structure:** 2 GCN layers for neighborhood feature extraction $\rightarrow$ 1 Fully Connected (FC) layer $\rightarrow$ Sigmoid output layer for binary classification.
- **Training Setup:** PyTorch, Adam optimizer, learning rate $0.01$, 200 epochs, trained on NVIDIA GeForce RTX 2080 Ti GPU. Validation set used for hyperparameter tuning.

### Baseline Methods (Benchmark Reference) `[RESEARCH FACT]`
- **Heuristic Graph Baselines:** Common Neighbors (CN), Jaccard's Coefficient, Adamic/Adar Index (AA), Preferential Attachment (PA).
- **Matrix / ML Baselines:** Matrix Factorization (MF), Decision Trees (DT), Random Forests (RF), Standard unweighted GCN.

### Evaluation & Paper Reported Results `[RESEARCH FACT]`
- **Metrics:** Precision, Recall, F1-Score, Area Under the ROC Curve (AUC).
- **Datasets Evaluated in Paper:** NYPD Arrests Data, Chicago Crime Data, UCI Network Data Repository.
- **Paper's Published Benchmark Figures (Reference Only — NOT SIH26189 performance):**
  - Common Neighbors: Precision 0.65, Recall 0.60, F1 0.62, AUC 0.67
  - Jaccard's Coefficient: Precision 0.68, Recall 0.64, F1 0.66, AUC 0.70
  - Adamic/Adar Index: Precision 0.67, Recall 0.63, F1 0.65, AUC 0.69
  - Preferential Attachment: Precision 0.64, Recall 0.61, F1 0.62, AUC 0.68
  - Matrix Factorization: Precision 0.72, Recall 0.68, F1 0.70, AUC 0.74
  - Decision Trees: Precision 0.73, Recall 0.70, F1 0.71, AUC 0.76
  - Random Forests: Precision 0.75, Recall 0.72, F1 0.73, AUC 0.78
  - Standard GCN: Precision 0.78, Recall 0.75, F1 0.76, AUC 0.81
  - CrimeGraphNet (Paper's Model): Precision 0.82, Recall 0.80, F1 0.81, AUC 0.85

### SIH26189 Relevance & Architectural Boundary
- **`[RESEARCH INSPIRATION]`**:
  - Confirms that link prediction is a viable framing for uncovering hidden ties in sparse, covert criminal networks.
  - Confirms the necessity of class-imbalance compensation (weighted loss or negative sampling).
  - Confirms that classical topological heuristics (Common Neighbors, Jaccard, Adamic/Adar, Preferential Attachment) must be evaluated as mandatory baselines against any neural approach.
- **`[PROJECT DECISION]`**:
  - SIH26189 uses **GATv2 (Graph Attention Networks v2)**, NOT isotropic GCN, as its candidate neural link prediction engine in Agent 3.
  - GATv2 provides dynamic attention weights across multi-relational edges (co-offending, phone calls, money transfers), allowing investigators to see *why* an edge was scored highly. GCN treats neighborhood weights uniformly based on graph degree.
  - This paper does **NOT** justify replacing GATv2 with GCN.
  - AI-predicted links are stored as `INFERRED` edges with explicit confidence scores and model versioning; they never overwrite source-backed evidence.
- **`[NOT ADOPTED / OUT OF SCOPE]`**:
  - Production deployment of CrimeGraphNet GCN code.
  - Uncritical adoption of paper's exact hyperparameters without local calibration.

---

## 2. Paper 2 — CrimeGNN

### Citation & Identity
- **Title:** *CrimeGNN: Harnessing the Power of Graph Neural Networks for Community Detection in Criminal Networks*
- **Author:** Chen Yang
- **Affiliation:** Shanghai Business School
- **Source Identifier:** arXiv:2311.17479v1 [cs.SI] (29 Nov 2023)
- **Local Artifact:** [`2311.17479v1.pdf`](file:///d:/AI-criminal-Network/2311.17479v1.pdf)

### Problem Definition `[RESEARCH FACT]`
- Focuses on community detection in criminal networks: identifying hidden, cohesive sub-gangs, cells, or operational cliques within larger networks.
- Challenges highlighted: Criminal networks are decentralized, fluid, covert, and actively conceal organizational boundaries. Traditional clustering methods relying on hand-crafted metrics struggle with non-linear graph topologies.

### Mathematical Formulation `[RESEARCH FACT]`
- **Graph:** $G = (V, E)$, with $V$ individuals and $E$ observed relationships.
- **Community Partition:** Partition $C = \{C_1, C_2, \dots, C_k\}$ of vertex set $V$, where each $C_i$ denotes an identified sub-community.
- **Objective Function (Modularity Maximization):**
  $$Q(C) = \frac{1}{2m} \sum_{i=1}^{k} \sum_{v_j, v_k \in C_i} \left( A_{jk} - \frac{d_j d_k}{2m} \right)$$
  where $A_{jk}$ is edge weight between $v_j$ and $v_k$, $d_j, d_k$ are node degrees, and $m = \frac{1}{2} \sum_{jk} A_{jk}$ is total network edge weight.
- **Optimization Target:** $C^* = \arg\max_C Q(C)$, parameterized via a neural mapping function $f: V \rightarrow C$.

### Method & Architecture `[RESEARCH FACT]`
- **GNN Encoder:** Multi-layer GNN propagating structural embeddings across edges to generate dense representations capturing local and 2-hop neighborhood structure.
- **Community Detection Module:** Maps learned representations into community assignment matrices optimized end-to-end via gradient ascent on the continuous relaxation of modularity $Q(C)$.
- **Training:** End-to-end gradient-based optimization using Adam optimizer (learning rate $0.001$, 50 epochs).

### Dataset Notes & Caveats `[RESEARCH FACT]`
- The paper explicitly notes: *"there is a lack of publicly available datasets specific to criminal networks due to privacy and legal restrictions."*
- To circumvent this, the author simulated criminal networks using:
  - Stanford Large Network Dataset Collection (SNAP): Social graphs from Reddit, Facebook, Twitter.
  - UCI Network Data Repository: General benchmark network graphs.
  - PADS Terrorism Network Dataset: Accused individuals in the Netherlands.
- **CRITICAL DATASET BOUNDARY**: These datasets are general research benchmarks or simulated social graphs. **None of them represent Indian operational criminal data.**

### Baselines & Evaluation `[RESEARCH FACT]`
- **Baselines:** Modularity Optimization (Louvain algorithm), Spectral Clustering (Laplacian eigenmaps + k-means), Infomap (random walk information flow / map equation).
- **Metrics:** Modularity ($Q$), Coverage, F1-Score.
- **Paper's Published Benchmark Figures (Reference Only — NOT SIH26189 performance):**
  - Modularity Optimization (Louvain): Modularity 0.61, Coverage 0.59, F1 0.64
  - Spectral Clustering: Modularity 0.63, Coverage 0.60, F1 0.67
  - Infomap: Modularity 0.70, Coverage 0.69, F1 0.74
  - TransCrimeNet / CrimeGNN (Paper's Model): Modularity 0.82, Coverage 0.81, F1 0.86

### SIH26189 Relevance & Architectural Boundary
- **`[RESEARCH INSPIRATION]`**:
  - Reinforces that community partitioning based on structural modularity provides an intuitive, mathematically grounded metric for criminal sub-group identification.
  - Provides a theoretical reference for evaluating how GNN representations capture cluster boundaries.
- **`[PROJECT DECISION]`**:
  - **NO AUTONOMOUS CRIMEGNN PRODUCTION SERVICE.**
  - SIH26189 maintains deterministic, explainable, classical community detection as its primary production standard:
    - **Louvain / Leiden algorithm** for modularity optimization.
    - **K-Core decomposition** for peeling peripheral nodes to reveal the dense core.
    - Executed deterministically in Python (NetworkX) or Neo4j Graph Data Science (GDS) library within Agent 3.
  - Classical algorithms are transparent, fast, deterministic, reproducible, and explainable in a legal/investigative context without training overhead or black-box neural optimization.
- **`[NOT ADOPTED / OUT OF SCOPE]`**:
  - Implementing an end-to-end neural modularity maximization network in the production codebase.
  - Altering planned GATv2 architecture to incorporate CrimeGNN.

---

## 3. Paper 3 — Graph Representation Learning for Street-Level Crime Prediction

### Citation & Identity
- **Title:** *Graph Representation Learning for Street-Level Crime Prediction*
- **Authors:** Haishuo Gu, Jinguang Sui, Peng Chen
- **Affiliation:** School of Information Network Security & School of Criminology, People's Public Security University of China, Beijing
- **Source Identifier:** *ISPRS International Journal of Geo-Information*, 2024, 13, 229 (Published 1 July 2024)
- **Local Artifact:** [`ijgi-13-00229.pdf`](file:///d:/AI-criminal-Network/ijgi-13-00229.pdf)

### Problem Definition `[RESEARCH FACT]`
- Spatio-temporal prediction of crime risk at the street-segment level (forecasting whether burglary or pickpocketing will occur on specific street segments in an upcoming 1-week window).
- Overcomes the Modifiable Areal Unit Problem (MAUP) and boundary discontinuities inherent to traditional arbitrary grid or census-tract aggregations.
- Exploits street network topology as physical conduits of human movement and crime diffusion.

### Sequential Processing Pipeline `[RESEARCH FACT]`
1. **Time-Varying Risk (TVR) Modeling:**
   - Mitigates extreme temporal sparsity and zero-inflation of crime occurrences on micro-street segments.
   - Applies a bi-exponential decay model based on collective memory theory (Candia et al., 2019):
     $$S(t) = \frac{N}{p + r - q} \left[ (p - q)e^{-(p+r)t} + r e^{-qt} \right]$$
     where $p+r$ represents communicative memory decay, $q$ represents cultural memory decay, and $r$ is the information flow rate between memories.
2. **Street Attributes to Vector (SA2V & SA2V_B):**
   - 12-dimensional vector of segment attributes: lanes, length, speed limit, bearing capacity, functional category, Uber H3 geometric index.
   - 26-dimensional block form feature vector (SA2V_B): building count, floor count, density, floor-area ratio (FAR) one-hot encoded.
3. **Street Network to Vector (SN2V):**
   - Transforms street network into a **Dual Graph** (Porta et al., 2006): nodes = street segments; edges = intersections connecting segments.
   - Generates 128-dimensional structural embeddings via **DeepWalk** (random walks with window $w=5$, walks per node $\gamma=10$, walk length $t=80$, Skip-Gram with negative sampling).
4. **Heterogeneous Information Network to Vector (HIN2V):**
   - Constructs a multi-relational HIN connecting street segments, Points of Interest (POIs, 789k), Areas of Interest (AOIs, 31k), business districts (311), and administrative districts (16).
   - Trains a 4-layer **Relational Graph Convolutional Network (RGCN)** on link prediction to derive 16-dimensional semantic embeddings.
5. **Downstream Binary Prediction Classifier:**
   - Concatenates $[x_{tvr}, x_{sa2v}, x_{sn2v}, x_{hin2v}]$.
   - Evaluates DeepFM and a 2-layer Deep Neural Network (DNN, hidden units 256 $\rightarrow$ 128, ReLU, L2 regularization $1 \times 10^{-5}$) for binary classification ($y \in \{0, 1\}$).

### Interpretability & Shapley Value Analysis `[RESEARCH FACT]`
- Computes Shapley values ($\emptyset_j(val)$) to assess marginal contribution of feature modalities:
  - HIN2V (heterogeneous urban facilities) contributed 45.06% to Burglary AUC and 63.80% to Pickpocketing AUC.
  - SN2V (street network topological embedding) contributed 44.29% to Burglary AUC and 19.17% to Pickpocketing AUC.

### Baseline Comparisons & Reported Metrics `[RESEARCH FACT]`
- **Baselines:** GLDNet (GRU + GAT/GGNN/EdgeConv), Logistic Regression, Decision Tree, Random Forest, XGBoost, Support Vector Machines (linear/RBF).
- **Paper's Published Benchmark Figures (Reference Only — NOT SIH26189 performance):**
  - GLDNet: Burglary AUC 0.506, ACC 0.572; Pickpocketing AUC 0.505, ACC 0.429
  - Random Forest: Burglary AUC 0.708, ACC 0.709; Pickpocketing AUC 0.718, ACC 0.692
  - XGBoost: Burglary AUC 0.760, ACC 0.495; Pickpocketing AUC 0.765, ACC 0.560
  - Paper's DNN Model: Burglary AUC 0.808, ACC 0.738, MSE 0.208; Pickpocketing AUC 0.805, ACC 0.721, MSE 0.226

### Research Relevance to SIH26189 `[RESEARCH INSPIRATION]`
- **Bi-Exponential Temporal Decay:** Inspires recency decay modeling for historical CDR communications and financial transactions in Agent 3 priority scoring.
- **Heterogeneous Information Network (HIN) Formulation:** Directly mirrors SIH26189's multi-entity schema (Persons, Phones, Bank Accounts, Vehicles, Locations, Cases) interconnected by typed relationships (`CALLS`, `TRANSACTED_WITH`, `ASSOCIATED_WITH`).
- **Shapley Value Feature Attribution:** Provides a proven method for generating explainable feature-contribution charts in Agent 3 investigative dossiers.

### STRICT OUT-OF-SCOPE BOUNDARY `[NOT ADOPTED / OUT OF SCOPE]`
- **STREET-LEVEL CRIME PREDICTION IS NOT IN SCOPE FOR SIH26189.**
- SIH26189 is a **Case-Centric Criminal Network Analysis System** built for investigating organized syndicates, fraud rings, and trafficking networks.
- It is **NOT** a patrol-routing system, predictive policing map, or citywide street crime forecasting tool.
- **Prohibited actions based on this paper:**
  - DO NOT create a street-segment prediction service or geographic forecasting module.
  - DO NOT build a DeepWalk random-walk pipeline.
  - DO NOT deploy GLDNet or DeepFM for street crime forecasting.
  - DO NOT replace criminal entity resolution with geographic location modeling.

---

## 4. Cross-Paper Research Synthesis

### Synthesis Matrix Across All Three Papers

| Dimension | Paper 1: CrimeGraphNet | Paper 2: CrimeGNN | Paper 3: Street-Level Crime Prediction |
|---|---|---|---|
| **Core Task** | Link Prediction (Missing criminal ties) | Community Detection (Gang sub-clusters) | Spatio-temporal event occurrence on streets |
| **Input Representation** | Graph $G=(V,E)$ + node/side attributes | Graph $G=(V,E)$ + topological structure | Dual graph + HIN (POIs, AOIs, streets) + temporal risk |
| **Neural Backbone** | 2-layer GCN + FC classification head | GNN Encoder + Modularity Optimization head | DeepWalk + 4-layer RGCN + 2-layer DNN / DeepFM |
| **Objective Function** | Weighted Binary Cross-Entropy Loss | Continuous Modularity $Q(C)$ Maximization | Binary Cross-Entropy / MSE on occurrence |
| **Sparsity Mitigation** | Inverse-frequency class weighting | Graph propagation across indirect paths | Bi-exponential memory decay smoothing |
| **Explainability** | Learned embedding dot-product | Modularity score ($Q$), partition coverage | Shapley value marginal feature attribution |
| **Primary Baselines** | Common Neighbors, Jaccard, Adamic/Adar, RF | Louvain Modularity, Spectral Clustering, Infomap | GLDNet, XGBoost, Random Forest, SVM |
| **Benchmark Datasets** | NYPD Arrests, Chicago Crime, UCI Repository | SNAP (Reddit/FB/Twitter), UCI, PADS Terrorism | Beijing 2017 Burglary (22k) & Pickpocketing (11k) |
| **SIH26189 Status** | Research Inspiration for GATv2 Baselines | Research Reference; Classical Louvain is Core | Feature Inspiration; Street Forecasting Out of Scope |

### Common Themes
1. **Topological Superiority:** In all three domains, leveraging graph connectivity consistently outperforms flat tabular algorithms (DT, basic LR, basic SVM).
2. **Sparsity & Covertness:** Real-world criminal data exhibits extreme sparsity and zero-inflation, necessitating specialized modeling (inverse class weights, negative sampling, or temporal smoothing).
3. **Mandatory Classical Baselines:** Neural architectures must always be benchmarked against established heuristics (Common Neighbors, Jaccard, Adamic/Adar, Louvain, Random Forest).
4. **Data Privacy & Scarcity:** All authors cite significant hurdles in accessing real operational criminal data, necessitating reliance on synthetic or public proxy benchmarks.

### Task Distinction & Boundary Enforcement
- **Link Prediction** (Paper 1) $\neq$ **Community Detection** (Paper 2) $\neq$ **Spatio-Temporal Crime Prediction** (Paper 3).
- These distinct tasks must never be blurred into a singular, ambiguous "AI Crime Model". Each serves a separate analytical objective with separate inputs, loss functions, and evaluation metrics.

---

## 5. SIH26189 Research-to-Project Mapping

| Research Concept | Source Paper | SIH26189 Subsystem | Adoption Classification | Implementation Stance & Boundary |
|---|---|---|---|---|
| **Link Prediction Formulation** | CrimeGraphNet | Agent 3 (Analytics Engine) | `[RESEARCH INSPIRATION]` | Validates mathematical formulation of missing-tie discovery. SIH26189 uses GATv2 with attention weights, not isotropic GCN. |
| **Topological Heuristic Baselines** | CrimeGraphNet | Agent 3 (Evaluation Suite) | `[PROJECT DECISION]` | Common Neighbors, Jaccard, and Adamic/Adar are required baseline comparators in the ML experiment ledger (`tracker.md`). |
| **Class-Imbalance Weighting** | CrimeGraphNet | Agent 3 (Model Training) | `[RESEARCH INSPIRATION]` | Negative sampling and loss weighting are adopted for training link prediction models on sparse case graphs. |
| **Modularity Formulation ($Q$)** | CrimeGNN | Agent 3 (SNA Engine) | `[PROJECT DECISION]` | Adopted as a structural quality metric for evaluating sub-gang cohesion, computed deterministically via Louvain/Leiden. |
| **GNN Community Detection** | CrimeGNN | Agent 3 (Experimental) | `[NOT ADOPTED]` | Not adopted in production. SIH26189 relies on deterministic, explainable Louvain/Leiden and K-Core decomposition. |
| **Bi-Exponential Temporal Decay** | Gu et al. (2024) | Agent 3 (Feature Engineering) | `[REQUIRES VALIDATION]` | Transferable concept for decay-weighting historical call records and financial transactions in priority lead scoring. |
| **Heterogeneous Information Networks (HIN)** | Gu et al. (2024) | Agent 2 & Agent 3 | `[PROJECT DECISION]` | Core architectural foundation: multi-relational graphs linking Persons, Accounts, Phones, Vehicles, and Cases. |
| **Shapley Value Attribution** | Gu et al. (2024) | Agent 3 (Lead Explainer) | `[RESEARCH INSPIRATION]` | Transferable for breaking down contributing features in AI investigative lead dossiers. |
| **Street-Level Crime Forecasting** | Gu et al. (2024) | N/A | `[NOT ADOPTED / OUT OF SCOPE]` | Explicitly rejected. SIH26189 is case-centric criminal network investigation support, not geographic predictive policing. |
| **DeepWalk Street Embeddings** | Gu et al. (2024) | N/A | `[NOT ADOPTED / OUT OF SCOPE]` | No DeepWalk pipeline will be constructed. |

---

## 6. Preservation of Canonical SIH26189 Architectural Decisions

Every concept stored in this research knowledge base strictly adheres to and reinforces existing canonical project decisions:

1. **System of Record vs. Analytical Store:** PostgreSQL is the authoritative system of record (`02_DATABASE_SCHEMA.md`). Neo4j is a rebuildable analytical projection (`03_GRAPH_SCHEMA.md`).
2. **Evidence Separation:** Source-backed evidence records (`OBSERVED`) and AI predictions (`INFERRED`) remain strictly segregated. Inferred links never overwrite observed edges.
3. **Role of GATv2:** GATv2 is planned for association scoring and link prediction under controlled evaluation gates (`trd.md`, `05_AI_CONTRACTS.md`). It is **NOT** a guilt predictor and **NOT** a kingpin oracle.
4. **Primary Explainability via SNA:** Centrality metrics (Degree, Betweenness, Eigenvector, PageRank) and K-core decomposition remain the primary explainable layer for investigator decision support.
5. **Evaluation Protocol:** Any neural model must demonstrate measurable improvement over Common Neighbors and Jaccard baselines under chronological splits with strict leakage prevention.
6. **Data Authenticity:** Datasets from academic papers (NYPD, Chicago, SNAP, UCI, PADS, Beijing) are strictly algorithmic research benchmarks. Synthetic Indian operational data (CDR, bank transactions) are explicitly labeled synthetic.
7. **No Code Modification During Memory Ingestion:** Storing research knowledge does not modify backend schemas, API contracts, GATv2 implementations, or service boundaries.
