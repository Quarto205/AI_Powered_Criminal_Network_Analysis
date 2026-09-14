# SIH26189 Canonical Contract
> Source: consolidated Gemini Notebook extraction of the SIH26189 project documents.
> Rule: do not invent unspecified details. Anything marked missing/uncertain/provisional must not be silently treated as final.

### SECTION 8: FRONTEND UI DATA CONTRACT

The frontend visual interface is designed to reduce cognitive load and avoid cinematic or sensationalized elements in favor of a clean, professional aesthetic.

#### 8.1 Visual Components [CURRENT/FINAL]

- **AppShell:** Persistent master navigation sidebar (Cases List, Global Search, Active Jobs Tracker, Security Settings).
- **CaseShell:** Display panel containing Case ID, Case Code, active jurisdiction, and tabbed navigation.
- **Overview Tab:** Visual widgets highlighting graph density, document counts, unresolved entity reviews, and active pattern alerts.
- **GraphCanvas (Cytoscape.js):** Render view for interactive neighborhood traversals.
- **GraphToolbar:** Interactive controls for filtering nodes and edges, adjusting temporal sliders, selecting layouts, and toggling ML predicted links.
- **EntityDrawer:** Slide-out drawer displaying canonical properties, associated cases, SNA centrality metrics, and aliases.
- **EvidencePanel:** Provenance window displaying supporting document source excerpts, text spans, page locations, and confidence parameters.
- **Timeline:** Time-based slider to navigate communications, transactions, and events.
- **PatternList / Alerts:** Panel showing matches identified by the rules engine, with direct investigative actions.
- **AuditPanel:** View of case logs, restricted to authorized roles.

#### 8.2 Graph Canvas Formatting Contract [CURRENT/FINAL]

- **Node Presentation Structure:** Nodes must display an entity-type icon, a stable name string, and a status indicator badge.
- **Accessibility Design:** Observable relationships (hard facts) must use solid lines, and AI-inferred relationships must use dashed lines. Status states must use redundant non-color indicators (such as text badges or styled patterns) to remain accessible.
- **Drawer Interaction Invariant:** Clicking a node or edge must open the detail drawer without navigating the user away from their current graph context.

---
