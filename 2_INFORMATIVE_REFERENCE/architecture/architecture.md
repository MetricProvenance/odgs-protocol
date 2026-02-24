
# ODGS Technical Specification: 00 - Architecture
**Status:** ISO/IEC 42001 Candidate Standard
**Version:** 3.3.0
**Type:** Normative

## 1. Abstract
The Open Data Governance Standard (ODGS) defines a **Hierarchical Constitutional Stack** for Data Governance. It strictly separates the Definition of Data (Legislative Plane) from the Execution of Data (Physical Plane), resolving the "Definition-Execution Gap" in High-Risk AI systems.

The core architectural pattern is the **"Sovereign Sidecar"**, where governance rules are enforced by a lightweight Interceptor that has *zero* hardcoded logic, relying entirely on immutable JSON configurations.

## 2. The Five Planes
The ODGS architecture is composed of five distinct planes of concern, flowing from human intent down to machine execution.

```mermaid
graph TD
    L[Plane 1: Governance] -->|Defines Policy| Leg[Plane 2: Legislative]
    Leg -->|Defines Metrics| Jud[Plane 3: Judiciary]
    Jud -->|Enforces Rules| ExBQ[Plane 4: Executive]
    ExBQ -->|Contextualizes| Phy[Plane 5: Physical]
    style L fill:#f9f,stroke:#333,stroke-width:2px
    style Leg fill:#bbf,stroke:#333,stroke-width:2px
    style Jud fill:#bfb,stroke:#333,stroke-width:2px
    style ExBQ fill:#fbf,stroke:#333,stroke-width:2px
    style Phy fill:#ddd,stroke:#333,stroke-width:2px
```

### Plane 1: Legislative (The Definition)
*   **Role:** Defines the semantic truth (What does "Revenue" mean?).
*   **Artifact:** `01-metrics-schema.json`, `ontology_graph.json`
*   **Immutability:** MUST be cryptographically hashed to prevent drift.

### Plane 2: Judiciary (The Enforcer)
*   **Role:** Validates data against the Legislative definition using logic expressions.
*   **Artifact:** `02-rules-schema.json`, `root_causes.json`
*   **Mechanism:** "Hard Stop" (ProcessBlockedException).
*   **Safe Execution:** Uses `simpleeval` for secure, non-turing-complete logic evaluation.

### Plane 3: Executive (The Context)
*   **Role:** Maps abstract definitions to specific business contexts (e.g., "Fiscal Year 2024").
*   **Artifact:** `runtime_config.json`, `physical_data_map.json`
*   **Responsibility:** The `OdgsInterceptor` (Sidecar) lives here.

### Plane 4: System (The Interface)
*   **Role:** Manages Input/Output and user interaction.
*   **Artifact:** Standardized CLI & API.
*   **Implementations:**
    *   **Python:** `2_INFORMATIVE_REFERENCE/src/odgs/cli.py` (Backend Ops)
    *   **Node.js:** `lib/index.js` (Frontend/Tooling)

### Plane 5: Audit (The Record)
*   **Role:** Provides forensic evidence of compliance (EU AI Act Article 12).
*   **Artifact:** `audit_log_schema.json` (Tri-Partite Binding).
*   **Storage:** Git-as-Backend (Zero-Trust Sovereignty).

---

## 3. The Sovereign Sidecar (Enforcement Mechanism)
The `OdgsInterceptor` is the core enforcement mechanism. It sits as a sidecar to any data process.

### Sequence Diagram
```mermaid
sequenceDiagram
    participant App as Business App
    participant Sidecar as ODGS Interceptor
    participant Git as Private Git Repo
    App->>Sidecar: 1. Request Operation (Payload)
    Sidecar->>Sidecar: 2. Calculate Input Hash (SHA-256)
    Sidecar->>Sidecar: 3. Sovereign Handshake (Verify Definition Integrity)
    Sidecar->>Sidecar: 4. Resolve Context Bindings
    Sidecar->>Sidecar: 5. Enforce Rules (Logic Expressions)
    alt Rule Violation
        Sidecar-->>App: 6. HARD STOP (ProcessBlockedException)
        Sidecar->>Git: 7. Commit Tri-Partite Evidence
    else Compliant
        Sidecar-->>App: 6. Access Granted
        Sidecar->>Git: 7. Commit Tri-Partite Evidence
    end
```

### Tri-Partite Binding (Article 12)
To meet EU AI Act Article 12 (Record-Keeping), every audit log entry cryptographically binds three elements:
1.  **The Event:** `SHA-256(Input Data Payload)`
2.  **The Law:** `SHA-256(Legislative Definitions)`
3.  **The Configuration:** `SHA-256(Runtime Context)`

This ensures that a log entry proves not just *what* happened, but *why* it was allowed/blocked at that exact moment in time.

## 4. API Surface
The system exposes a lightweight FastAPI interface (`2_INFORMATIVE_REFERENCE/src/odgs/system/api.py`).

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/sovereign/intercept` | POST | Main enforcement point. Accepts process URN and data context. Returns GRANTED/BLOCKED. |
| `/api/sovereign/logs` | GET | Verification endpoint to view the immutable audit trail. |
| `/api/sovereign/hash` | GET | Returns the current master hash of the governance definition (The "Passport"). |

## 5. Normative References
*   **EU AI Act**: Article 10 (Governance), Article 12 (Logging).
*   **ISO/IEC 42001**: Control B.7 (Data Management).

---
[< Back to README.md](/README.md)
 | [Documentation Map →](index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)
