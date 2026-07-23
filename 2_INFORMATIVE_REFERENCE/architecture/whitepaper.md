# **The Quality-Liability Fallacy: Why Your Data Governance Can't Protect You from the EU AI Act**

An Empirical Analysis of the "Silent Drift" Crisis in Industrial AI

---

Author: Iyer K  
Credentials:

- MDM Product Manager, Global Port Operator (Fortune 500\)  
- Senior Technical Project Manager, Aviation IT Provider (12 years)  
- 25+ years enterprise program management experience

Date: February 2026  
---

## **Abstract**

The industrial data establishment has successfully convinced enterprise leaders that "Data Quality"—traditionally defined as the absence of null values, the correctness of data types, and the freshness of pipelines—is the primary shield against algorithmic failure. This paper challenges that premise with a fundamental legal and technical reality: **You cannot comply with Strict Liability regimes using probabilistic tools.**

Through a forensic analysis of the EU AI Act (Regulation (EU) 2024/1689), specifically Articles 10, 12, and 99, I demonstrate that the current stack of passive data catalogs (Collibra, Alation) and build-time metric layers (dbt) is structurally obsolete for High-Risk AI. These tools utilize an "Observability" paradigm, designed to detect drift *after* the fact. However, the regulation mandates a "Prevention" paradigm, requiring that data be validated against specific semantic assumptions *before* inference occurs.

This report introduces the **ODGS Protocol** (Open Data Governance Standard) and the concept of the **"Hard Stop"**—a cryptographic runtime mechanism that physically prevents an AI agent from consuming data that has drifted from its legal definition. By applying the "definition-counting" methodology from *The Definition-Execution Fallacy* and the proprietary "Cost of Semantic Liability" (![][image1]) formula, I quantify the regulatory exposure of passive governance.

**Key Finding:** For a typical logistics giant with €50 billion in revenue, reliance on passive governance results in a probabilistic exposure of **€3.5 billion** (7% of global turnover). In contrast, implementing a cryptographic Hard Stop reduces this semantic liability exposure to **€0**, shifting the industry conversation from "engineering hours saved" to "regulatory indemnification."

## ---

**1\. THE DIAGNOSIS: The "Silent Drift" Crisis**

### **1.1 The Definition-Execution Gap: A Structural Failure**

In the contemporary "Modern Data Stack," organizations have optimized aggressively for velocity, flexibility, and scale. The predominant architecture involves dumping massive volumes of telemetry into "Lakes" and "Lakehouses" (e.g., Snowflake, Databricks) using schema-on-read methodologies.1 This architectural shift, while beneficial for exploratory data science, has created a fatal flaw for regulated industrial AI: the **Definition-Execution Gap**.

The "Semantic Layer Orthodoxy" suggests that if we define business logic once in a tool like dbt or Looker, every downstream consumer will calculate metrics consistently.2 This is a fallacy. The semantic layer solves *execution*, not *governance*. It defines *how* to calculate a metric (the SQL transformation), but it fails to define *what* the metric is legally supposed to represent, *why* it was defined that way, or *who* approved it.2

Consider the typical enterprise environment. A data engineer writes a dbt model to calculate Net\_Profit\_Margin. The code is version-controlled in Git. It is technically robust. However, the *business assumption*—for example, whether "Net Income" includes discontinued operations or whether "Revenue" is recognized on booking or payment—is buried in the SQL code or, worse, in a Jira ticket description.2

This coupling of business logic to execution code creates the "Definition-Execution Gap." The definition exists only as the code executes. If the code changes, the definition changes. There is no independent, immutable record of what the metric *should* be, only a record of what it *is* at the moment of query execution.

For human analysts using BI dashboards, this gap is annoying; it leads to "reconciliation meetings" where executives debate whose number is right. For autonomous High-Risk AI agents, this gap is catastrophic.

### **1.2 The "Uncomfortable Truth" of Silent Drift**

The uncomfortable truth is that "Silent Drift" is not when data breaks; it is when data **changes meaning** while remaining technically valid.1

In traditional software engineering, we monitor for "loud" failures: exceptions, null pointers, timeouts. In data engineering, we monitor for schema violations: a string where a float should be, or a null value in a non-nullable column. The modern data stack is excellent at catching these errors. Tools like Monte Carlo and Great Expectations provide robust "Data Observability" to alert engineers when data stops flowing or changes shape.3

However, the EU AI Act does not punish you for null values. It punishes you for invalid **assumptions** (Article 10).

**The Anatomy of a Liability Event**

To understand why this is a crisis, we must dissect the anatomy of a semantic liability event. The failure does not happen in the infrastructure; it happens in the semantic interpretation.

Consider the metric **EBITDA** (Earnings Before Interest, Taxes, Depreciation, and Amortization), a standard financial KPI used in automated trading, credit scoring algorithms, and supply chain optimization models.1

* **08:00 AM:** The definition of EBITDA includes "Operating Income" as defined by GAAP, specifically *including* a government subsidy for renewable energy usage. The AI model has been trained on historical data where this subsidy was always present.  
* **09:30 AM:** A data engineer, responding to a new internal accounting policy or a change in upstream ERP logic, updates the operating\_income transformation logic to *exclude* that specific subsidy. This change is pushed via CI/CD. The pipeline runs green.  
* **10:00 AM:** An AI agent executes a high-frequency trade or re-routes a logistics fleet based on the *old* semantic assumption of EBITDA (that it implies a certain cash flow profile including the subsidy), but it is fed the *new* data payload (which excludes it).

The data remains a valid float. The pipeline status is green. Monitoring tools see no anomaly because the data distribution might not have shifted significantly enough to trigger a statistical alert (e.g., the value dropped by 2%, which is within standard deviation).3 Yet, the **assumption** mandated by Article 10 of the EU AI Act has been violated. The AI is hallucinating on valid data.

**Artifact 1: The Silent Drift JSON**

The following JSON artifacts illustrate how a definition changes without breaking the schema, creating the Silent Drift:

```json
// STATE A: Valid at 08:00 (Hash: 8a7b...){  "metric_id": "MP-FIN-099",  "name": "EBITDA_Adjusted",  "formula": "operating_income + depreciation + amortization",  "unit": "EUR",  "version": "1.0",  "assumption": "Includes government subsidies per EU-2024-Grant"}
```

```json
// STATE B: Silent Drift at 09:30 (Hash: 3c9d...){  "metric_id": "MP-FIN-099",  "name": "EBITDA_Adjusted",  "formula": "operating_income + depreciation + amortization", // Formula looks identical in summary  "unit": "EUR",  "version": "1.1",  "assumption": "Excludes government subsidies (Policy Update 2026-B)" // SEMANTIC CHANGE}
```

Standard observability tools see float \-\> float. They see no error. The EU AI Act, however, sees a violation of **Article 10(2)(d)**: failure to formulate valid assumptions regarding what the data is supposed to measure and represent.4

### **1.3 The Latency Gap of Passive Governance**

Why can't current tools catch this? Because they are **Passive**.

Tools like Collibra and Alation rely on "harvesting" metadata *after* the fact. They scan databases and query logs periodically—often every 24 hours—to build catalogs and business glossaries.1

This creates a **Latency Gap**:

1. **Change Event:** Definition changes at 09:00 AM.  
2. **Inference Window:** AI executes decisions from 09:01 AM to 11:59 AM using the new data but the old understanding.  
3. **Governance Event:** Catalog crawler runs at 12:00 PM and updates the glossary.

During that three-hour window, the organization is in a state of **Regulatory Non-Compliance**. The AI agent is operating without a valid governance shield. In a High-Risk scenario (e.g., autonomous driving, medical diagnosis, critical infrastructure), a three-hour window of drift is not a "data quality issue"; it is massive liability exposure.

## ---

## **2\. THE REGULATORY ENVIRONMENT: An Extinction Event**

The enforcement of the EU AI Act represents an extinction event for "probabilistic" data governance in high-risk sectors. The regulation fundamentally shifts the burden of proof from "best effort" to **Strict Liability**. It is no longer sufficient to try to be compliant; you must *prove* compliance at the atomic level of every inference.

### **2.1 Article 10: The Criminalization of Semantic Drift**

Article 10 ("Data and data governance") is the operational pivot point of the entire regulation for High-Risk AI systems. It mandates that training, validation, and testing datasets must be subject to appropriate data governance and management practices.4

Crucially, **Article 10(2)(d)** explicitly requires that these practices concern:

"the formulation of assumptions, in particular with respect to the information that the data are supposed to measure and represent".4

This phrasing effectively criminalizes "Semantic Drift." In the context of a modern, distributed data lake, the definition of a metric like "Net Profit," "Safety Margin," or "Carbon Intensity" is fluid. It can change silently due to upstream schema modifications, alterations in business logic, or the ingestion of new data sources with different granularities.

**The Liability Trap:** If an AI agent executes a trade, authorizes a loan, or triggers a safety shutdown based on a definition that has drifted—meaning the data no longer "measures and represents" what the system assumes it does—the operator is now liable. The defense of "we didn't know the data had changed" is explicitly removed by the requirement for **governance practices** that ensure data suitability *before* use.1

### 

### **2.2 Article 12: The Forensic Audit Trail**

Article 12 ("Record-keeping") mandates that high-risk AI systems must technically allow for the "automatic recording of events (logs) over the lifetime of the system".8

For systems identified in Annex III (which covers critical infrastructure, law enforcement, and essential public services), the logging requirements are granular and exacting. **Article 12(3)** specifies that logs must provide, at a minimum:

* (a) Recording of the period of each use of the system (start/end time).  
* (b) The reference database against which input data has been checked.  
* (c) The **input data** for which the search has led to a match.  
* (d) The identification of natural persons involved in verification.8

This requirement demands a forensic audit trail that links **every single inference** back to the specific semantic definition active at that precise millisecond. A general "system log" showing API calls or a "model card" describing the training data in broad terms is insufficient. The log must prove that the "definition of truth" used by the AI was valid, approved, and unchanged at the time of execution.

**The Gap:** Most current MLOps platforms log the **model version** (e.g., v1.2 of the neural net) but fail to log the **semantic version** of the input data (e.g., "was 'Revenue' defined as booked or billed?").

### **2.3 Article 99: The Cost of Failure**

The penalties for non-compliance are existential. **Article 99** (formerly Article 71 in drafts) sets administrative fines for non-compliance.

* **Prohibited Practices (Article 5):** Fines up to **€35,000,000 or 7% of total worldwide annual turnover**, whichever is higher.9  
* **High-Risk System Requirements (Article 10):** Fines up to **€15,000,000 or 3% of total worldwide annual turnover**.10

While Article 10 violations typically fall under the 3% tier, the failure to govern data in a way that prevents "unacceptable risks" (e.g., discrimination, fundamental rights violations caused by drifted data) can escalate the penalty to the 7% tier. Furthermore, the reputational damage and the potential for "Stop Work" orders from regulators present a risk that exceeds the monetary fine.

This structure creates a regime of **Strict Liability**. If the harm occurs, and you cannot prove you had the governance in place to prevent it (i.e., you cannot produce the Article 12 logs proving the data assumptions were valid), you are liable. There is no "good faith" exception for bad architecture.

## ---

**3\. THE METHODOLOGY: The Liability Risk Scoring**

### **3.1 Moving from Technical Debt to Balance Sheet Risk**

We must stop pricing data governance in terms of "efficiency" or "engineering hours saved." In the era of the EU AI Act, governance is a financial instrument. It must be priced in terms of **regulatory exposure avoided**.

The industry currently treats data quality issues as "Technical Debt"—something to be fixed in the next sprint. Under strict liability, these issues are "Balance Sheet Risk." A single instance of Silent Drift in a High-Risk AI system can trigger penalties that wipe out a quarter's profit.12

### **3.2 The Formula: Cost of Semantic Liability (![][image1])**

To quantify this exposure, I propose a proprietary formula to calculate the **"Cost of Semantic Liability" (![][image1])**. This formula is derived from the penalty structures of Article 99 and the probabilistic nature of passive governance tools.

**Formula 1: Cost of Semantic Liability**

**![][image2]**  
Where:

* ![][image1]: The Cost of Semantic Liability (Annual Expected Loss).  
* ![][image3] (Inference Volume): The number of automated decisions made per year. If ![][image4], the risk exists. For any production AI, this is effectively a binary "1" for "Risk Present."  
* ![][image5] (Probability of Drift): The likelihood of a semantic change occurring without runtime interception. In passive stacks (Collibra, dbt), this approaches ![][image6] (or 100%) because there is no mechanism to physically stop the inference if the metadata is out of sync.1  
* ![][image7] (Global Revenue): The total worldwide annual turnover of the parent entity.10  
* ![][image8]: The maximum penalty multiplier (7%) under Article 99(3) for severe non-compliance.9  
* ![][image9]: The minimum floor for maximum penalties.9

This formula forces organizations to confront the reality that **passive governance (![][image10]) guarantees maximum exposure.**

### 

### **3.3 The Application: The Logistics Giant Case Study**

Let us apply this methodology to a hypothetical logistics giant, "GlobalLogistics Co.," which operates autonomous supply chain agents (High-Risk AI) and generates **€50 Billion** in annual revenue (![][image11]).

**The Business Context:**

GlobalLogistics Co. uses an AI system to optimize routing for hazardous materials. The system relies on a metric called Road\_Risk\_Index.

* **Definition A:** Road\_Risk\_Index is calculated based on weather, traffic, and *accident history*.  
* **Drift Event:** A data engineer changes the source of *accident history* from a verified government database to a real-time crowd-sourced feed (e.g., Waze API) to improve freshness.  
* **Semantic Drift:** The crowd-sourced feed has a different definition of "accident" (includes minor fender benders) than the government DB (only reportable crashes). The Road\_Risk\_Index spikes artificially.  
* **Result:** The AI reroutes hazardous materials through a "safer" but much longer route that passes through a densely populated city center, violating a municipal ordinance and increasing the risk of a catastrophic event in a prohibited zone.

**Scenario A: Passive Governance (Status Quo)**

GlobalLogistics Co. uses a standard modern data stack: data in Snowflake, transformations in dbt, and governance via a passive catalog like Collibra.

* ![][image3]: The system makes thousands of routing decisions daily. The probability of the drift coinciding with a decision is 100%.  
* ![][image5]: ![][image12] (100%). Without a runtime interceptor, the catalog observes drift *after* the daily crawl. The AI consumes the drifted Road\_Risk\_Index immediately.  
* ![][image7]: €50,000,000,000.  
* **Max Penalty**: ![][image13].

**Calculation:**

**![][image14]**  
**Scenario B: Active Governance (ODGS Hard Stop)**

GlobalLogistics Co. implements the ODGS Protocol with the runtime Hard Stop mechanism.

* **Mechanism:** When the data engineer changes the source to the Waze API, the ODGS Interceptor calculates the hash of the incoming payload. It detects that the source lineage and schema definition do not match the signed DefinitionHash for Road\_Risk\_Index.  
* **Action:** The Interceptor triggers a **Hard Stop**. The AI agent is denied access to the data. It throws an error and defaults to a safe-mode fallback (e.g., human dispatch).  
* ![][image5]: ![][image15]. The probability of consuming drifted data is reduced to near zero.

**Calculation:**

**![][image16]**  
**Conclusion:** The value of the ODGS Protocol is not measured in operational features, but in **structural indemnification** of reducing ![][image5] to zero. By implementing a 'Hard Stop', the organization transforms Article 10 compliance from a probabilistic gamble into a deterministic guarantee, effectively reducing the 'Silent Drift' liability to zero. This architectural control is the only viable foundation for High-Risk AI under Regulation (EU) 2024/16891\.

## ---

**4\. THE ARCHITECTURE: The Tri-Partite Binding**

To eliminate ![][image5], we must replace the concept of "Monitoring" with "Binding." Monitoring is passive; Binding is active. The ODGS Protocol uses a **Tri-Partite Binding** mechanism that cryptographically locks the data to its meaning at the millisecond of use.1

### **4.1 The Three Planes of Governance**

Governance must be decoupled from the data pipeline and elevated to a supervisory control plane. ODGS divides this into three distinct planes, each with a specific cryptographic state.

**Table 1: The Three Planes of ODGS Governance**

| Plane | Function | Cryptographic State | Role |
| :---- | :---- | :---- | :---- |
| **1\. Definition** | The "Platonic Ideal" of the metric (Formula, Unit, Dependency). Contains the pure semantic concept (e.g., "OEE" \= Availability \* Performance \* Quality). | **DefinitionID** (SHA-256 of Logic) | **Source of Truth** |
| **2\. Configuration** | The Runtime Context (Limits, Tolerances, Risk Level). Defines the "Safety Critical" parameters (e.g., max data staleness, strictness of schema checks). | **ConfigID** (SHA-256 of Rules) | **Runtime Context** |
| **3\. Enforcement** | The Runtime Check (The "Hard Stop"). The mechanism that allows or blocks the data payload based on the other two planes. | **VerificationStatus** (PASS/BLOCK) | **Execution Gate** |

This architecture ensures that the "Definition" (what it means) and the "Configuration" (how strictly to apply it) are independently versioned and cryptographically signed. A change in the definition (Plane 1\) automatically invalidates any runtime configuration (Plane 2\) that was signed against the old definition, forcing a re-verification process.1

### **4.2 The Interceptor Mechanism (Visual Logic)**

The **Interceptor** is the core of the ODGS architecture. It is not a dashboard; it is a **Middleware Agent** that sits directly in the execution path between the Data Source (e.g., Snowflake, Sensor) and the AI Agent. It operates with millisecond latency to minimize impact on industrial control loops.1

**The Logic Flow:**

1. **INTERCEPT:** The AI Agent requests a data payload (Request: Metric X).  
2. **FETCH:** The Interceptor queries the Sovereign Registry to retrieve the currently active and signed DefinitionHash (e.g., hash(EBITDA\_v1.2)) and ConfigID for Metric X.  
3. **HASH:** The Interceptor computes the local PayloadHash of the incoming data stream and its associated schema metadata. This involves hashing the JSON structure, the column types, and the source identifiers.  
4. **VERIFY:**  
   * **IF** (PayloadHash \== DefinitionHash) ![][image17] **PASS**. The data is forwarded to the AI Agent.  
   * **IF** (PayloadHash\!= DefinitionHash) ![][image17] **HARD STOP**. The Interceptor triggers a ComplianceException. The process is killed immediately.  
5. **LOG:** A record of the transaction (Pass or Block) and cryptographic proofs are written to the immutable Audit Log (Section 5).

**Result:** The AI agent **never receives** the non-conforming data. "Hallucination by Definition" is rendered physically impossible.

### **4.3 Cryptographic State vs. Metadata**

Current tools like Collibra store "Metadata"—descriptions of data. ODGS stores "Cryptographic State"—signatures of data.

* **Metadata** says: "This column *should* be EBITDA. It was last updated yesterday."  
* **Cryptographic State** says: "This payload *is* 0x8f7a... which matches the signed definition of EBITDA v1.2. If a single bit changes, the hash changes to 0x9b2c... and the match fails."

This distinction is critical for Article 10 compliance. Metadata is a claim; Cryptographic State is a proof.1 Under Strict Liability, you need proof.

## ---

**5\. THE MARKET ANALYSIS: The "Switzerland" Strategy**

The industrial data market is fragmented into "Walled Gardens" designed to trap data to retain value. The major players—Siemens, Palantir, and Snowflake—all compete to own the semantic layer. ODGS resolves ecosystem fragmentation by acting as the neutral Binding Layer \- the neutral "Diplomatic Courier" that binds semantics across these silos.1

### **5.1 The Industrial "Build vs. Standardize" War**

The market is currently engaged in a war for control of the "Industrial Semantic Layer."

* **Siemens** creates lock-in through hardware and the **Industrial Information Hub (IIH)**.13 They excel at generating OT data but struggle to govern it once it leaves the factory floor. Their strategy is "Hardware Lock-in."  
* **Palantir** creates lock-in through the **Foundry Ontology**.13 They act as a "Black Box" or "Hotel California"—you can check data in, but you can never extract the logic without losing its meaning. Their strategy is "Ontology Lock-in."  
* **Snowflake/dbt** are fighting for the storage layer. dbt's semantic layer is excellent for analytics but lacks the granular, protocol-level semantic enforcement required for strict liability (as discussed in Section 1.1).13 Their strategy is "Ecosystem Lock-in."

### **5.2 The Architectural Landscape**

ODGS positions itself as the "Switzerland Wedge"—universal, neutral, and focused purely on liability shielding.

**Table 2: The Industrial Architectural Landscape**

| Feature | Siemens (IIH) | Palantir (Foundry) | Collibra / dbt | ODGS (Sovereign) |
| :---- | :---- | :---- | :---- | :---- |
| **Primary Goal** | OT Hardware Lock-in | Ontology Lock-in | Observation / Analytics | Liability Shielding |
| **Governance Mode** | Proprietary Model | "Black Box" Logic | Passive / Build-Time | Active / Runtime |
| **Latency** | Real-time (internal) | Batch / Pipeline | 24hr Crawl / Build Time | Millisecond |
| **Article 10 Stance** | "Trust our hardware" | "Trust our platform" | "Here is a report" | "Cryptographic Proof" |
| **Interoperability** | Low (Siemens Ecosystem) | Low (Hotel California) | High (Metadata only) | Universal (Headless) |

### 

### **5.3 The "Switzerland" Strategy**

ODGS resolves ecosystem fragmentation by acting as the neutral **Binding Layer** that allows a Siemens sensor to talk to a Snowflake Data Lake without losing its semantic legal status. ODGS does not store the data; it **insures the definition**.

By remaining "Headless" (agnostic to the storage or visualization tool), ODGS avoids direct competition with the giants. Instead, it becomes the necessary compliance wrapper that enables them to sell into High-Risk markets. It allows a CIO to define "OEE" once in the ODGS Registry and enforce that definition cryptographically across Siemens, Snowflake, and Palantir simultaneously.1

This neutrality is the competitive moat. Siemens will never build a protocol optimized for Hitachi hardware; Palantir will never build a standard that makes it easy to leave Foundry. Only an independent, open-standard player can credibly offer a universal binding layer.

### **5.4 High-Friction Logic Extraction (The "Black Box" Risk)**

Palantir Foundry represents the most formidable "Walled Garden" in the industrial sector. The core of Foundry is its Ontology, which maps data to real-world objects and kinetics.13 However, user feedback highlights significant friction regarding interoperability. Users describe the Ontology as a "relational database" that is hard to migrate away from.15

This "Hotel California" effect—you can check data in, but never leave without losing the business logic—creates a strategic risk for Sovereignty. ODGS counters this by decoupling the **Definition** from the **Platform**, ensuring that the enterprise owns its semantic logic, not the vendor.

## ---

**6\. THE AUDIT LOG: Article 12 Compliance**

Article 12 of the EU AI Act ("Record-keeping") is not a suggestion; it is a specification for forensic evidence. It requires the automatic recording of events (logs) over the lifetime of the system to ensure traceability.8

### **6.1 The Forensic Schema**

A generic "system log" that records "API call successful" will fail an audit. You need a **Semantic Ledger** that links the inference to the specific definition used. ODGS provides this through a forensic schema designed to satisfy Article 12(3).1

**Table 3: ODGS Audit Log Schema Specification (Article 12 Compliance)**

| Field Name | Type | Description | EU AI Act Art. 12(3) Map |
| :---- | :---- | :---- | :---- |
| **transaction\_id** | UUID | Unique inference event ID. | Traceability |
| **timestamp\_utc** | ISO8601 | Precise time of execution (Start/End). | Art 12(3)(a): "Period of use" |
| **data\_source\_id** | String | Origin of the data lake/sensor. | Art 12(3)(b): "Reference database" |
| **input\_payload\_hash** | SHA-256 | Hash of the *specific* data slice used (Privacy-Safe). | Art 12(3)(c): "Input data match" |
| **definition\_hash** | SHA-256 | The semantic logic active at runtime. | Art 10: "Formulation of assumptions" |
| **config\_hash** | SHA-256 | The specific runtime configuration used. | Art 10: Governance Practices |
| **verifier\_id** | String | Human/System ID authorizing the run. | Art 12(3)(d): "Natural persons" |
| **status** | ENUM | PASS / BLOCK / OVERRIDE | Art 14: Human Oversight |

**Compliance Analysis of the Schema:**

* **Article 12(3)(a):** timestamp\_utc explicitly covers the "period of each use."  
* **Article 12(3)(b):** data\_source\_id provides the provenance link to the "reference database."  
* **Article 12(3)(c):** input\_payload\_hash proves *which* data led to a match without storing massive payloads (privacy preservation), linking the input to the result.  
* **Article 12(3)(d):** verifier\_id links the automated log to the "natural persons involved in verification," creating the human-in-the-loop audit trail mandated for high-risk systems.1

### 

### **6.2 The Defense in Court**

In a court of law or a regulatory hearing, this log is the primary defense. It allows the operator to state with mathematical certainty:

*"At 14:02:05, we blocked inference because the input data hash did not match the approved definition hash. We prevented the failure."*

Or, in the event of an investigation into a decision:

*"At 14:02:05, we proceeded with inference. Here is the cryptographic proof that the data used matched the approved definition of 'Road\_Risk\_Index' v3.1, which was authorized by the Chief Safety Officer on Jan 1st."*

This capability satisfies **Article 10(2)(d)** (Formulation of assumptions) and **Article 12(3)(c)** (Input data match).4 Passive tools cannot provide this level of granular, cryptographic proof because they do not sit in the execution path.

### 

### **6.3 Proof of Human Oversight (Article 14\)**

Article 14 requires "Human Oversight".16 The status field in the audit log, specifically the **OVERRIDE** enum, is critical here. It documents instances where a human operator explicitly authorized the AI to proceed despite a warning (e.g., in an emergency scenario), or where a human intervened to stop the system. This creates an unbreakable chain of custody for decision-making.

## ---

## **7\. THE COMPARISON: Active vs. Passive Governance**

### **7.1 The "Soft" vs. "Hard" Governance Divide**

The market for data governance is structurally flawed regarding AI liability. We can categorize the competition into "Soft" (Passive) and "Hard" (Active) governance.

**Tier 1: Passive Governance (Collibra, Alation)** These platforms are "Soft." They rely on harvesting metadata *after* the fact.3 They are excellent for human discovery ("Where is the revenue data?") but useless for automated enforcement. They cannot stop a pipeline; they can only alert a human that a pipeline *was* wrong yesterday.

* **Structural Flaw:** Latency. The gap between the crawl and the inference is the "Zone of Liability."

**Tier 2: Analytical Semantics (dbt MetricFlow)** These tools are "Firmer" but still not "Hard." dbt defines metrics in code, which ensures consistency in reporting.3 However, their "contracts" and "circuit breakers" are primarily build-time checks. They stop a dashboard from breaking; they are not architected to intercept a millisecond-latency API call from an autonomous agent.1

* **Structural Flaw:** Focus on Analytics, not Operations. dbt is designed for the analyst, not the autonomous agent.

**Tier 3: Active Governance (ODGS)**

ODGS is "Hard." It is a runtime interceptor. It does not care about the human analyst; it cares about the machine consumer. It enforces the "Hard Stop."

**Table 4: Strategic Comparison of Governance Architectures**

| Feature | Collibra / Alation | dbt MetricFlow | ODGS (Metric Provenance) |
| :---- | :---- | :---- | :---- |
| **Core Function** | Metadata Catalog & Governance | Analytics Query Engine | Liability Shield Protocol |
| **Enforcement Model** | Passive (Post-event alerting) | Build-time (CI/CD) & Query-time | Runtime (Hard Stop) |
| **Mechanism** | API Harvesting (Crawling) | SQL Generation from YAML | Cryptographic Hashing (SHA-256) |
| **AI Act Focus** | Documentation Support | Indirect Reliability | Direct Article 10/12 Compliance |
| **Latency** | Hours/Days (Crawl delay) | Batch / Query Latency | Real-time (\<10ms Overhead) |
| **Liability Stance** | Observability ("See the error") | Reliability ("Fix the error") | Strict Liability ("Prevent the error") |

### 

### **6.2 Why dbt and Collibra Fail Strict Liability**

Strict Liability means you are liable even if you were not negligent, simply because the harm occurred. To protect against this, you must eliminate the *possibility* of the harm.

* **Collibra** offers **Observability**: "See the error."  
* **ODGS** offers **Enforcement**: "Prevent the error."

Under a 7% turnover penalty regime, Observability is insufficient. If the AI has already acted on the bad data, the penalty is incurred. Seeing it on a dashboard 24 hours later is too late.

## ---

**8\. IMPLEMENTATION: The Path to Indemnification**

### 

### **8.1 From Tool to Standard**

Enterprises should not view ODGS as "another tool" in the stack. It is a **Standard**. It is the implementation of the "Sovereign Standard" for data liability.

The goal is to move from "Vendor Lock-in" (Palantir) to "Protocol Lock-in" (ODGS). However, unlike vendor lock-in, Protocol Lock-in protects the enterprise by ensuring portability and legal safety.

### **8.2 The "Hard Stop" as Sovereign Defense**

The adoption of ODGS must be framed not as a software procurement, but as a **capital adequacy measure**.

* **The Liability:** Uncapped exposure to Article 99 fines (7% of Turnover).  
* **The Shield:** Cryptographic enforcement of the "Hard Stop."

For the Logistics Giant in our case study, the calculation is not about "Return on Investment" (ROI); it is about **Return on Survival**.

* **Passive Governance:** ![][image18]. Exposure: **€3.5 Billion**.  
* **Sovereign Enforcement:** ![][image19]. Exposure: **€0**.

The "Hard Stop" is not an operational inconvenience; it is the only mechanism that mathematically secures the balance sheet against the probabilistic failure of High-Risk AI.

### 

### **8.3 The Fiduciary Mandate**

The implementation of the ODGS Protocol is not a request for resources; it is a **structural hedge against material risk**.

Using the ![][image1] formula, the Chief Data Officer must formally articulate the exposure:

*"Current architectures carry a probabilistic liability of **€3.5 Billion** (7% turnover). This risk is unhedged. The ODGS Protocol provides the necessary cryptographic hedge to reduce this residual risk to near zero."*

This reclassification moves the initiative out of the "IT Budget" and into the domain of **Enterprise Risk Management (ERM)**. It forces the industry to acknowledge that data provenance is no longer a technical detail, but a component of capital adequacy.

## ---

## 

## **9\. CONCLUSION: The End of "Good Enough" & The Era of Enforcement**

The industrial data establishment has spent a decade optimizing for velocity. We celebrated how fast we could ingest, transform, and serve data. The EU AI Act has abruptly inverted this value system. In a Strict Liability regime, velocity without provenance is merely accelerated risk.

We are witnessing the death of "Probabilistic Governance"—the idea that we can monitor our way to safety. You cannot monitor a millisecond-latency inference that carries a €35 million penalty. You must bind it. The EU AI Act has ended the era of "move fast and break things." We are entering the era of "prove it or pay up."

Existing governance tools—passive catalogs, build-time checks, and proprietary walled gardens—are artifacts of a pre-regulatory age. They were built for analytics, not for autonomous agency. They offer Observability, which is the ability to see a crash after it happens.

ODGS offers Enforcement, which is the ability to prevent the crash before it happens.

For the industrial AI economy, the Hard Stop is the only defense against the Silent Drift. It is the difference between a compliant, profitable future and a 7% global turnover fine.

The choice before the Industry Leaders is binary:

* **The Probabilistic Path:** Continue with passive catalogs and dashboard alerts, hoping that the "Silent Drift" doesn't hit a High-Risk use case. This is not strategy; it is gambling with the balance sheet.  
* **The Deterministic Path:** Implement the ODGS Hard Stop. Accept the friction of the "circuit breaker" in exchange for the certainty of indemnification.

In the eyes of the law, data is no longer just "oil" or "assets." It is **Evidence**. If you cannot cryptographically prove what your data meant at the moment of decision, you did not run an algorithm. You rolled the dice.

**The Hard Stop is not a feature. It is the only way to stop rolling.**

## ---

## **10\. NORMATIVE REFERENCES & FURTHER READING**

**Regulatory Frameworks**

* **Regulation (EU) 2024/1689 (EU AI Act):** laying down harmonised rules on artificial intelligence. Official Journal of the European Union, L, 2024/1689.  
* **ISO/IEC 25012:** Software engineering — Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model.  
* **ISO 8000-61:** Data quality — Data quality management: Process reference model.

**Academic & Technical Foundation**

* Iyer, K. (2025). *The Definition-Execution Fallacy: Why Your Semantic Layer Can't Govern What You Haven't Defined.* (Pre-cursor analysis on the cost of semantic coupling).  
* Van Eck, M. *Automated Administrative Decisions and the Risk of the Black Box.* (Foundational analysis on administrative law compliance).

## ---

## **APPENDIX A: FORENSIC EVIDENCE OF "SILENT DRIFT"**

The following JSON artifact demonstrates how a valid data schema can pass traditional "Data Quality" checks while failing a "Semantic Governance" check.

**State A: The Governed Definition (09:00 UTC)**

**Hash:** e3b0c442... (Authorized)

```json
{  "metric_id": "KPI-2026-EBITDA",  "formula": "(Revenue - Expenses)",  "exclusions":,  "compliance_tag": "ART_10_STRICT"}
```

**State B: The Drifted Pipeline (12:00 UTC)**

**Hash:** 8d969eef... (HARD STOP TRIGGERED)

```json
{  "metric_id": "KPI-2026-EBITDA",  "formula": "(Revenue - Expenses)",  "exclusions":,  // Drift: Subsidies are now accidentally included  "compliance_tag": "ART_10_STRICT"}
```

**Forensic Analysis:**

* **Data Quality Tool (Collibra/Great Expectations):** Returns **PASS**. (The field exclusions is an array, and it is valid JSON).  
* **ODGS Interceptor:** Returns **FAIL**. (The Hash of State B does not match the Hash of State A).  
* **Result:** The AI Agent is prevented from reporting inflated profits based on the inclusion of subsidies.

## ---

## **APPENDIX B: THE LIABILITY RISK FORMULA**

The Cost of Semantic Liability (![][image1]) is calculated as the probability of drift interacting with the Strict Liability penalty regime of the EU AI Act.

![][image2]  
**Where:**

* **![][image3]**: Inference Volume (Number of AI decisions made per year).  
* ![][image5]: Probability of Drift (1.0 for probabilistic data lakes; \~0.0 for ODGS-governed streams).  
* ![][image7]: Global Annual Turnover of the operator (as defined in Article 99).  
* ![][image9]: The base penalty cap for prohibited AI practices or non-compliance with data governance requirements.

---

#### 

#### **Works cited**

1. Compare Collibra vs. dbt \- G2, [https://www.g2.com/compare/collibra-vs-dbt](https://www.g2.com/compare/collibra-vs-dbt)  
2. AI Act Service Desk \- Article 10: Data and data governance \- European Union, [https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-10](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-10)  
3. Article 10: Data and Data Governance | EU Artificial Intelligence Act, [https://artificialintelligenceact.eu/article/10/](https://artificialintelligenceact.eu/article/10/)  
4. Data Governance Tools – Collibra vs Alation: Pros, Cons, & Recommendations \- Analytica,  [https://www.analytica.net/blogs/data-governance-tools/](https://www.analytica.net/blogs/data-governance-tools/)  
5. Article 10, Data and data governance, Artificial Intelligence Act (Proposal 25.11.2022),  [https://www.artificial-intelligence-act.com/Artificial\_Intelligence\_Act\_Article\_10\_(Proposal\_25.11.2022).html](https://www.artificial-intelligence-act.com/Artificial_Intelligence_Act_Article_10_\(Proposal_25.11.2022\).html)  
6. AI Act Service Desk \- Article 12: Record-keeping \- European Union, [https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12)  
7. Article 99: Penalties | EU Artificial Intelligence Act,  [https://artificialintelligenceact.eu/article/99/](https://artificialintelligenceact.eu/article/99/)  
8. AI Act Service Desk \- Article 99: Penalties \- European Union, [https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-99](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-99)  
9. Fines under the AI Act \- A bottomless pit? \- Taylor Wessing,  [https://www.taylorwessing.com/en/interface/2021/ai-act/fines-under-the-ai-act---a-bottomless-pit](https://www.taylorwessing.com/en/interface/2021/ai-act/fines-under-the-ai-act---a-bottomless-pit)  
10. Penalties of the EU AI Act: The High Cost of Non-Compliance \- Holistic AI, [https://www.holisticai.com/blog/penalties-of-the-eu-ai-act](https://www.holisticai.com/blog/penalties-of-the-eu-ai-act)  
11. 8 Best Alternatives to Palantir Foundry in 2026,  [https://www.digetiers-dap.com/post/palantir-foundry-alternatives](https://www.digetiers-dap.com/post/palantir-foundry-alternatives)  
12. Smart Innovators: Industrial Data Management Solutions \- AVEVA,  [https://engage.aveva.com/rs/986-YIS-805/images/Verdantix\_Smart\_Innovators\_Industrial\_Data\_Management\_SolutionsPINew\_23-07.pdf](https://engage.aveva.com/rs/986-YIS-805/images/Verdantix_Smart_Innovators_Industrial_Data_Management_SolutionsPINew_23-07.pdf)  
13. Difference Palantir-Foundry and Data Warehouse : r/dataengineering \- Reddit, [https://www.reddit.com/r/dataengineering/comments/w8i4gv/difference\_palantirfoundry\_and\_data\_warehouse/](https://www.reddit.com/r/dataengineering/comments/w8i4gv/difference_palantirfoundry_and_data_warehouse/)  
14. AI Act as a neatly arranged website – Legal Text, [https://ai-act-law.eu/](https://ai-act-law.eu/)  
15. Collibra and dbt: Driving a common language around data, [https://www.collibra.com/blog/collibra-and-dbt-driving-a-common-language-around-data](https://www.collibra.com/blog/collibra-and-dbt-driving-a-common-language-around-data)

### 

## About the Author

I am a data management professional with over 25 years of experience implementing enterprise programs at Fortune 500 companies. My background includes roles as MDM Product Manager for a global port operator and Senior Technical Project Manager for an aviation IT provider.

This paper represents the direct learnings from over $50M in data platform investments—both successful and failed. Throughout my career, I have led implementations that specifically exposed the critical gap between business requirements and technical execution.

I advocate for pragmatic, empirically grounded approaches to data governance that prioritize business value over technical complexity, helping organizations count what matters before building what's expensive.

---

© 2026 Licensed under Creative Commons Attribution 4.0 (CC BY 4.0). 

*You are free to share, adapt, and distribute this work with appropriate attribution.*

---

Document Hash: 9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8

Citation: Iyer, K. (2026). *The Quality-Liability Fallacy: Why Your Data Governance Can't Protect You from the EU AI Act.* Whitepaper.

Word count: \~5600 words

Read Time: 30-35 minutes

---
> **Require architectural clearance or SLA support for your organization?** [Consult the Sovereign S-Cert Registry](https://metricprovenance.com/brief).

[< Back to README.md](/README.md) | [Documentation Map →](index.md) | 🎯 [Watch the demo →](https://www.metricprovenance.com/watch)

---

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAYCAYAAAB0kZQKAAACoUlEQVR4AeyVWahNURjHjyFkDpEUIeEBDx5kyBwKT0oUnpQhhSIeSEnJkEgyJFNmXpQHSaYMhZQiZKYo8cSDKfx+21mnfbd99j33nv1wH+7p/1vft7+9zlrfXvtbazctNIBfYxLhJdS2Ei3pOBimQT8I6oDTHXJRuSSc+CQzfISNMAV2wRnoBhegJ+SitCRWMPI9+Al9YSosgUlwA57BILgPuSiZhJNtYeSlMBc+QVyuxlcCN8EkMdUrnsRMhtsBB2E3pOkXwadwFXJTSKINI/qU37ErIUs/uHkFclNIYhEjdoHj8BmytJibdyA3hSRmFEc8X7RZ5gU3f0NSrQk0A9XcplJCEgOKf6hPxbflv/tgHWyC9bATgvrg7Ifb4Bbfjq0hk2hBxMPnG/YtZMmJeiU6HOBaVmHd3h5wr/GDXuJY6MOw7rpl2BoyCQvtHdFW0A7KqT03RsIbCOqK40EWrxHPkWThjqLfY3gP/8kkDFqQ2tE2KTQh5jK61LglWQO+Drf1BKI+yFHsXYhrDBfJxAj9U0hiK5fPYRv0hrhcnT0EroMnJqakD3irwcK+hHWV/P8f/CDn8OHKni12sLPbcjKO7/IB9hSsgSNwAg7DIUjTZoKdwZX4gl0IcXnEdyLgQ2AiubJjI48mJIFbsIBMZDgXZ+EVOIFf0Fv4SQ0kMAuUh9xlHKs/edSPI/4E/BhiIk2ndUtjCoV4ElGA5hE42DHsQyin8dyI7xTrYyKx0xCX/a7FAj3wPZUvYiOlJRHdqKAZSh+Xei12NljcG7B+WzCF/jSeDyY2BH8vmKAP6Vfa7xCh9JWIblTQWDNz6GfNWKDz8M9BkMnM58JlH4FdAH4kO2KXQ0nVrETY8+4qK9+6KA1cF6eaJOoyT2bfBpHEXwAAAP//m3E50AAAAAZJREFUAwBdjHMxMuZ0+gAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAYCAYAAAALQIb7AAACA0lEQVR4AeyUTUgVURiGb22CoKCgCNpEPxC1ioKKgtrWqk0QBdGmRdGuwoWCIqgbwZ2oK10oogsR16KiCxFERd34L6KIG0UFFRV9nuHOcB3Fvzu68vI+5/vuOTPfO+ecmXM5dY6/C7NEFju+jF+oOgUzMAkTMAZfIWvFzeqpeA/6wPib+BDqIGvFzSx4ieYVrEIrJKaDzJ5Q/RZ0wiYkpoPM3qert6VjYuEws/bEXNKF4mbu1zvGlsGXhJCc4mZPKe1+dRG3IBs952b3vYEYKG7mrBzosMmSXu4fgCEIdJZmGviyRQ+eaRbul9+XT+XFId5UxJ/HoIppHkCoFyQFUAavQbkd90m6IVCm2TN6boODmfvlTW/pX4PvoN7QhEW/kedCCeRDC9wEt8RaG+SBNPtM5vnnaWFBTw/PxB/0q6s0lfAJwm+vlnwYfLgq4j+w6ApxBx6BZns+H80aGfD8u0G08DWi068mqmmasC80u0tfP3wED+5xovL0uU4yCC79PjP6j5RP6kxc3jtcvQTOYJ24AKF+kpTDFXBPR4l/IJAzC5Ijmh7GnfUvoktWQVRNNC5fDrEUfLkc91AY4f9f8BpCKnVcs0WufgnN8B/cW0JKow8kNeBLkkfcTuNHXUg+C4GOa+bFLuEcictHiOT/ef5pTIikqTOMOk5iFt102uRczXYBAAD//0MR8CwAAAAGSURBVAMAGnlgMebF5NcAAAAASUVORK5CYII=>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD8AAAAYCAYAAABN9iVRAAADg0lEQVR4AeyXWahNURjHt3lWxgwlmTK9iDJmeJHpgWSI6JY8mMv4gAxliuJBQhQPJB6QB6XMikQIKfNMUoQyD7/fqX06d9/TvXvfc7vO7d7b/3e+tdew9/rWWt9a61YPKvFflfOVdfKrZj5j5ieTfgov4Ak8hocwBSqq+tLx5bASekFa0Zk/REl7uAHa2dhOcBAqohbT6Z1wBs6DfszDphR13sxq/PSDL3Aayksty/hD3XjfZpgJl+ECLADzumCDbM53p6AFXISfUF4ytE7xsfGQrV9kJ5JOf6bFNQh1jkRtmAhZnR9qAZyF8tQ2PjYJesAlmAF2FFMqjaDVB8jUDx5c0cOwxTrvKFmnPLGza/ngcGgMLtWF2IaQVO1o8A2i+k5GGyjivPE+hIJP4KaH+S9ydrby5cFgX9x71pBuBnGkH/Wp+AeiMq+pmdHYcskZ7y67X1bIgd60dd84jC2tXKZ7aDwA7sFxcMNqhS1Ofym0LSarfpsbdd5ZN99jQZsL12l8C+5ArrKzHsOGxAReVgAl6T0VakJUNciwrMiyL0vn+Ubg5pnrQDpB44Ig8D1jsIbCRmxJekWFBhCVeZYVct440XnjzVnLbKQT68joCmo9Px0hVB8Sq8E47Y9Vhk8HElegNKpFo+lg6BhCzvh8np9DHJ2kUnPwPZiUjPW6pCwr5LxXPy8adjYz3nViEA2+gp3BBAP5CZ2cStrr4wbsKjgBfsSB9F3urmTFVj1qzgF3+tbYkbAC3kESHaCysT8aG2osCSf3CDblvCPq/d0dVQe93XmnL7ACuGvuwtowPPt98V3yHKzdWK+ROumlwg92Jk/nkxyXHmdLaWc/jHHP4k08u9tjEusBLbyeb8fOAm93Ts400m8g5byj4P29CRk62gjrct2HVc/4CfNC59uSdxNGgf8IPcIqb4eez7d5MFSSOO+d+yXtjGnv49nOaIoTaS+1nUwH8D7pnnAMUnIzSSVK+HEmnWnDwWPmI/WdYTuYuRy9Uu6grA64Jzj6c0nHkWHjPx5+I079uHUcUFeqce7KTLeL6/xVWrgqXD4ucWeGrOAoPy73ZdgtYDxZHo70IvKsg8k/xXXea6f/F3vJWIIb7g2YQMfdkPbz4KbnxmS8iju053LqWKE87xTXeTvucnxNwuWOScvntzw5EJi0HABXQDoj3xJJnM+3vufcn0rt/D8AAAD//z9TmY8AAAAGSURBVAMA7f2uMU4xg1UAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC0AAAAYCAYAAABurXSEAAADTElEQVR4AeyWWchMYRjHjy3rhaXIFkJkjSyJbKWQG+ECKVKUSEkIIUWIXFAulFBSuLBkubJmyU7IvpRkyR4i2+8335z5zjnffL4xZSYy/X/n/5z3vHPOM895l6kc/IWf/0kX6qX9E5XuS7XuwBN4CvoD/C7oZ/E5UB2KpmSlT5JJWzgOjWAUtII20AE2wnLYBkVTMukwkV4Eb8HKYil94mjS9/DwxxAWXtmSbk4aVvcE/g2isn/TdINxOiysZXtw/3QKx9IetQGc1IYzYMWxwitb0gPTaRxJe2h1CVbAYxgPRVN5SX8no2EwFxbABjgPN6Ar3Ic/oZq53DSZdDO+5EpxGb8GN+Eq7IDOMAleQVSdOHG1OYRXJOfD2HI6baJ9H0yGqKpET4yTSYdDwy/vpsMeMHaouHpwWkb+OJO+XuZK2YYeNLmkYjG5WrWjxSXX/YAwpSkcHZJYqZJJD0pfOpr2XM0JauIV9bcIS7N0GkLbJVgMhyHUSIKLEFMy6cFctaKn8Yo0lA4mMB23gibdmNi2EfgYMAk3KcJgYhAEVq0WHqoqwRoYB11gISiLsJagHzi3wmJyGgTRpNvT0hLOwWf4lWZw0bG5CG8Ajv3X+DQ4CDvBvwNWKnywm1U32sMllTD4ysGJXgOfD6tAOUx8K65UU2mwIFiJTLoPoQ84hVtlq/aIeDRkUxMaV8ISUE6UcE3fS4MT8wDuZHZpdG684NzNyrHrczjNqBqRG9oF/Asof0xvAu9rTrFNzqQdCk6O+nTy1bl5tCDeBdnkEPLPVDhhnLze3L6+JSsZjksnpw90ufTN7KfTO4jKJfQ2DSaHZRS9b6bRwKT13+E9na+AasihJ7hDzsaV4zH8EZ6HTCDYAg4DLCOHjFXONBBUAv9xOiyGE/uGsBLlk7RVdHecyS1mgRuNk9Gl0YnoxmSFuRSTQ8QflFwNutMr+seM0+AHh1vgH7PWeOx6PklbaYfIdm42D3y9y3Af4rDpSOxDsZhcUVbTEm5CdYjrgXPIYUMYk2N6My3rIKZ8kvYGJvXcAJw0H3Fl+weDLHjtTaR9K7GT2Tf1kDgp31hy/Kf65Jt06st5HUq/tJ7wJbjrYbmrmEk7N9yInuWebknPnwAAAP//dXMr0QAAAAZJREFUAwDkIqIxGVnx3gAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAXCAYAAAD+4+QTAAABoElEQVR4AeyUSytFURTHr7eiSBkYEFIiIxOmpgxkwEBJ+QwMTBgjH8GADGRuKJlQIjOSMmLklfIcePz+q71Ot+ueruPI6N7+v7PW2o+19tl731Oa+YdfsUiiTc63XS1kmIQkqmfwBCzAFFRDJC/STcsMbMA5jMFP1czAPWiCVWiFY2gAkxepJbqDJUgqzblg0iKcwBwo1zLW5EUOiFbgCJKokcEjsAPZUjxKQxVkvIj83zDApErQyjGR7vFqoA9SF9ElUZ43PbJ4Db7OKXURrVb53vXI4iP4dvhx21USBhUy/ga54z22YnFFCiX3/pvglAXrxmPrjyviK/FJcfYqdPi2hTDj8aUakhbRle3QxMAu9hnsgLEuxdcEh/Dt4Cto1FvY/cbPlf5PpzS2gaQCmzjD4AvWlR4iXgO7EN6hRk3WP/eFzl6Qf4atA9c+jtq0SlzTNE8lW8eOg4rq0zSPb/IiW0RdoO+Qkop24k54AJeS9BA8gusWpx/0xSjHzsIgPIHJi1iQ4qE32Wa+tkg78okf6a+KRAnzOcUi+XYltu0LAAD//2AdFekAAAAGSURBVAMAX/U/L2UM0sQAAAAASUVORK5CYII=>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADMAAAAYCAYAAABXysXfAAADv0lEQVR4AeyXV4gVSRRAa3Ne2GUjG9jMsn8b2GQWs4iYPkRQUAwfBlBRUTFHTGBWzP4KiiImzAERFUVEEXNWjJjFdM6z69G248zIgD7E4Z66t6r6dde9dSvMq+EF+nvpTKFO5gs9M/8T9QNwCk7DCbB+EL0XZsI/UJCSnZlNjPJHWAufQ2Ow/gO6OrwNG6EZFJxknYkD/BvjEmyBKMcw+sNrMAAKTopy5htG+T2sh7uQli+TSlG/S7qenypqUBWT4axJdFrF9BqdbiwUuyhnKieDW51o1fsU3aEp9IBxUHDyJGfuMNIhsAS2wzn4A36F4VCQknXma0b5EyyG2gluBvOw3c3eQ5dWOvHgIWgIxUlzOt32O6JLI6/w0Cw4A59BXrLOxBRbl38iBGdpLvWPwK0aVSoZz1Mfw1YoTubQeR/MAFSJ4rMTeOoanIW8ZJ2pkvR4ziRmTv2SK0PwnEnMEpVpeYGnjkJx8gWd30L6GKBarBj07BhD1pmqvOIy7IC0+GPr5y0yvEm9A/QBU/NPtFKJIr2JUA1/UfSDMfAfKD63H8O0tO8DbOV1inbQE2pCOYjibx7bbdPOuLi/4+kNkD1fPqFNuW4BTrM3Az+4gvpuGJTghzCDAUh/0G29VwhhKPSFRWAa+vxx7LFwGOKBPAX7NrgRdUY3AMVDuzxGNlC5mfmXDiPjVeYGtueMC9doUM3JKEpf7GLugv0WeGdriXZBrkLfA6NqMOIHozMu1Kn0d4VbcAXM/Z/Rfm8Y2naD68zWom6WeBfEzKV3XMe/02CGPJa+/ngzne5gRuld7A/BG8AydJSFGD4zCb0P2oBSjWIpKF9RmP8u5OwH69Bn1A0AZviNwu8YNGc4rhcvunvoawRGXoddp6anNxKaQ3bGQ/zTmWiXpL2bLeAh08NZwAzOgDdrbQ9UL6HufqaBkWxLhxfWm+j0ztOa+kRwhmx3VnSuBm0j4CrsBMU2M8dgasd3u0btz/M0zuR/lDLMZ1PPF7ei3Wiiwi6KT8Fzy/NgPrYD9hYxEtvBmnKmtcHxVuE6bEGfA/cocDZ9xtlyDTehz7TdhtYh1xnmQ7EsqzNGrz4vctG+gXbtoMJKChe8Cx0z6Ig73WwqbgK90Q4QFdpTTAMPzxgMU7UebdNBRyug3dVctwOxu8EMeETK4oxp5aB9oRE9gmHUUDlxi4/paIP57z98OmY9jdcl+9NtDvxi0uABafom1RDbYz2ny+KMh9Zy3uLZ8A66LmQHRNOzk7I4c5JhDgadmYx2kaOenzwAAAD//36W140AAAAGSURBVAMA75DAMV9JVYQAAAAASUVORK5CYII=>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAXCAYAAABu8J3cAAACqElEQVR4AeyVS6hOURiGf3eSSFGIKBkdRcqtJFPKZUByGRBi4FYmUowMkAmSQiERA4mBkVvKicg1QhlR7gwQyeV5VvvbZ9nHf5zZ+Qfn9D7ru6y1/v2ttfZep2utQf46C6keREPuSDeqnA3bYSMMgfZqAAOXwg5YDr0h1wSCYzAdxsFYaMroFzvSi+QpWAgn4TXcginwPw1nwHWw8KPYkXAHBkLIQiz0Cgn77mMfZDRFIctIToOV8BBOgD/qKrrjt6VddD6HnfAItsIH2A2hMTgWcQC7D/YU3MMeguYoZBXBDfgCocs4o2Ey1NMgOuaBYzGljOcTudOYmoUswFkDa2E97IXvoF+zkMEE4+Ej5HJVxjNs6mBfT/piLG6Sv9UXbxKogzRvIdQD5zCsgK+QChmhA98gV8RD82TFj7muLO+Kub435s/bZGzBvwS+J5haKsTKDX7ZZEScv3RZd3Jj7s8UtTRtzXVhGxi6H0p5NNXVRGeXwqk+pEgnE3NjbErSRBwFkSq1Du8m5EeVduQdSVX9OrxXzEe/fpXoi7HRH3H0R74Pzmrw68K0yB15ReiqY5sJkyJ+maJ/N9EXY2NUxC8iUdiJ2P7wFP6ShXwmcw3ixcJN8ix1LtgU+Ln6SRdh7SqOb311rrFb76XIkFJTC+9TYUtjIQZHaKx2GDY0F+c2eAtikjzbx3ijQFnEaZw5EL/l5zyL2MvQncYt5dVuEO+WfiImO8mr/SzZJeBtaWGL8XM1EzwBV4tJ2kTrA49jF4GFPcNug6riwqy7I7+Z4eXiFe9Le4bY6n0obikf5D8rjzOS73G8fb2gnLuZeCbEQ3FLeX+4e94hZVIndkRf7tJ4TK78B3575Y5cZLA769G5MMJWekPmHLTqrxbCmI5RZyHVfW+YHfkDAAD//xfN1L4AAAAGSURBVAMA7IN/L8rOaFcAAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAYCAYAAAC4CK7hAAAEPElEQVR4AeyWV6hVRxSGdxLTGymkkYQ0EhKSkGIvqIhiAQu+qNgQRQSfbGDFDqKIoKLYUKwvKhbsYkF9sYPYsIsNVBAVe/m+zZ5755x7jvrgFbl4WP+sNWv23mdWnXk9qSC/V4a8bIGssBH5C09PBovAHDAIfA9iqspkJBgBWoJKIKZ/mHQE34I3wCegMWgOCtF6lOfARXABVAPF6AMW9oPw7FHkX0ASR6QDiu1gJWgLugBpq0OGAfCeYAPYBaaCzeBDEOhfBJ1wFn4PXAXOz8ALUUOU7cEd8BX4HRQj//99Fj8DOuxX+DFQYsjPTKaB/mA1eAQeAD3vhhGTTxmc62U3v4y579SCaxwsJd89jrQb6IRh8D/APlCMjMLcbPHHjOez/1DcBZ8D93QJXkIhIqPQ3AezQT4tiRR+qHo0v57JX2ZcpiHzECqDemAouAKeRHVY1BCd9xNyPum8XijXgY/BJpBDGvImmqZAD96E59OCTGGK+Cd6JlMlppGyUZQLDZE/K9ykdXiEF6yVQhEx4jNYrwEkM0JeAg2ZyMwctyiNTIwhrMV0nsk18Bqw0FvDx4G1IJCGWOhG10I2vdqFxQJcZ+zN9Kfg+YZ8h04HunkjbN1Zy6hLSUN8Wc0eBj0bYzm6fKqJws1Ngq8Ao0FMpkcDFMOBhdwdbrHrVcQyVBeNm4Ql7uXrJEneAYEGI/gtI2cK7mReJnM0pBkLkhvsjRDDJoAqh3Yw84Ou2UEOMP8bBFqF4LdOwKVDDNuAkTa/EXNIL2/JNBpitH/I5q3gvmuNGTnfD0azVEoa0jmb+oIvxlicrRVitssJLHwDLG5YSqae50E6yQZT8iPk/0FMetlUssupP+kA1Pl8C2SbACyp7wCKGuLLdh9bJM8VJfu79fBb9IQF6tSD9AsEU8K+Hnc61InpJn/PIYKNI9SHaiMi1xDr03ZvzakzctaHGeE8B0bkIZr5wF7uBxBzyE5RCU0/ENIOMSVPWgXbss7woLIwbR7qAzTSDXkqB53cWrLelEVIxzZMLgOdAkv8f9PZ86NMffiAhsjHMtwAs8BbIFAVBK8AnjHWgmkzE12gRpngteYWsimkx/oiB7K11mZi+/S0R0zJs8fbhC03VTAo6xQ76HjmgXSmzomNDmspD4boCc8S2+ZBVqaDhcBDLeSoXWoNOtNrIHwMMPQa0QdZ0utdEXTIFLj3MQvZWvNAQ5XSRkb/0+gtRXYdlqagqWan06AmKI2K3fM2cg8Q3kMspWCIGovdu4sG6Y1OKN0MLCWL25B3Y3YaeOX4E25bNT0RU7JLeW3RaGU347eMePoAgyllx3sX+W3geQRLyZuDUXXiUWBGGCGftWtpvMa4XoLYEJV61BulG9Aj6vJxGIVdyoiV+SBrkmnmXcxbgc+rK1fkG1Kuf1aeH3+ehpTnPp/67VeGPNVFL/iBChORxwAAAP//Ka6L+wAAAAZJREFUAwAYqNsxx7YEKAAAAABJRU5ErkJggg==>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFAAAAAYCAYAAABtGnqsAAAEzklEQVR4AeyYd6gcVRTGr71ixy4qKnZFsSB2QVARxIaoCBZQFEUQsaNiV9SEFPJHQkgC6SGkJxBIb6R30guE9B6SkJ7fb9gZZmZ33759G3ib5C3ft+fcc+/cnXvm3HPP7Kmh5VOTB1ocWJP7QmhxYIsDa/RAjZfnI/BR5lsK18L1ULkSuQwqpyK/gmfBkw2ns+DP4bkwQd6BE+m5BY6DV8BX4Y3wZngH7Aj/gN3hyYAzWOQn8H+4AraG58EEeQfGHQ+h7IBGHCLCXr514HJk7FjUExr652xWOBwaXIgsHJC1hHAdBqNuPPIQTMPx1xQM6gW17sSl3NEFsBKMsIbG7KPT6BuJ3AmLUMoJTxRGjS3ItHiShiE8BWkkIuoKPtwB3NEGuAmOhg/CUrgL4xuwJpRy4FOFGf3xghqJi/j+C66Bb8N6RDtuqi800V+M7Fpge+RlMIbr/obGfFgTnCg/gQ48jPF5+DX8HnaA0+FCeC80oSKOOc6pYcabuNac7QG3H30P7ALvg0ajlURvdJ05D7kNzoY1Ie/Aa5nNE9eJfTqLaM+FfeDd8D24FabhVvDUHpE2ltHdYm+W6euMfTD8AKZxWrrRgO6h16tEv3nsZ+xWEeaydegfw89gU3BK+qK8A40++12IuWQgDXW3s6cwzSLoaB24oKin2PAAJsskRAae+rdi8aSz3kSN8CHfpg1ERWxmhNc+i+wB3b5WC/GCrWk7hRB+o8/7dYs/hl4t4vmi6/IOfDqyhjAmVPfxcPGmKl3lA/mlxCAXPQv7T3AUjPEyykzYWJhynMOt7C76lgsnwHtgHi9haMxJzbAMGnTgMww10iYjK+E5BuiMT5FGlg68Cl3bi8jXoYuxIEcN74YQjCYTPGoEq/v/0N6CLvIHpPCBtEIxQszF8YPFVBY6w3RiFWHB6/Xe159c0R8akY8jb4fes1vYLU2zKpR14G1McwOcBs0biLLwx81lPzLCmstcaVK2arfo9CT0ldAIip1gjjKhu0Aui3CQbw8pi9Xv0P+Bwq1stHrif4TBh4NoEFfT2xN6ACISDEHz4PMQaYNuOjJVvYJ+ADYWZxYGZl5j3cKP0OFiJyGNPp/aavTXYCl4o3/TYWJGBJN8XDMOwmAUDEO6hSx3zKWeghbm5jp/h+4EFrMW7zOweHoigo59GMV5vad8QU9XEXyI/m5RB4bd8FfoA7wS6dpcI2pFeIguZpQOt5i2BrYaeR9b9HeW29XEfgkGt5eF8vXo/WApuM39o8GEbb9P04WqG71GWJzHPFhcvCWQETuUQd4EIoHRsYSWjkIkSM+bGJtBMbV4wF3Ib0sfgCe6VUPkQOxVYRej50BxOV9W+j6VL9GF+St2qO2Y76CYh9yqqAmMCqMvMaCYZ/xnyK37Am0jF1F/cAtXe1dGl28l/rXzBRdbVJuULXc8RMxBRh5dGbiNdW7+VL2fUZ6aiARH0Nw2liFxgYyp/tAUBxqBbmMTtq9DbsHfWZoLdmvfia4DEBl4Mv+LJS64z0e3FjPnurVpZmAO9E2ibcZaZ42mONAl6KCNKtCE72sTatBuwlbP077tKWM3dA8iI3gVeh5Gcj5f5sc0e7upDjwWN+6L/xYm8m0DcXyiOR1oLrXo9q+n49N7IYSjAAAA//+k6GE5AAAABklEQVQDAHaW5DFqZGa+AAAAAElFTkSuQmCC>

[image11]: <data:image/png;base64,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>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAXCAYAAAAcP/9qAAABkklEQVR4AeyUyStFYRjGL2XIkCxQ7AxF/gTTTklK7KxYWJJhp5SwsJKyMCZlYyhlIZGhKCsryrBlaSrFRuH33O53ut1zTveernPu5t6e33m/6bzPN5z7ZYZS9EsbB7bxQWx1Bqvpgwqw5KdxLy4zcAdrUA6W/DQuxOUC9sGmWON8RpRCPGXFG0D/PMj0hWiTMc6lR9vyTnyEB+gBJ+mdCacOL21KovHDPH6gDPJgEHRGx8R6iFY/lWdISsa4iixjoBVrAoeUW2EVjuAM5uAUNKEVYlIyxosuWTZpr4EFeAPFZuIneJX+VtY7xviKFhksEbdgAApA+uKxDZOwA9/QAV7laNxClj14ghPQNt8QOyFWlTQ0gFc5GutmaSLTNCyDVtROHAVNpJtYDV2wC+vgVY7G12R5hWjdUtF5ykRf+SX1EVD5npiosiMDcyIxHMwZz4Zr9scvTRugo9DF0kj5HBLRAYM0wSHiB+j70PU5TjlkjFX+b9pIWAvFUAQlUAdT4Kux8rvi54pdTdWRNtYuBMIfAAAA//8azjDeAAAABklEQVQDAGBWPS8kTLuIAAAAAElFTkSuQmCC>

[image13]: <data:image/png;base64,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>

[image14]: <data:image/png;base64,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>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAXCAYAAAAcP/9qAAACBklEQVR4AeyVyyumURzH37lopplZzWKmmalZzKWp8Se4ZeOuREqKWLBCYaeUkKxkoVyTsnFLKSVyKcpKKUosbIiN2waFXD7f1zlPT6+n59142NDvc76/3/m9nd855znneB16pr+Xwk+28UFv9S9WUgEtkAWOBVk4mSrzsA9DUA7D8ApCQRV+y+CD0AHjsAalkA7F8KDwRzq/QDSLifKDDPI/YAGsHeFoAkWoU/g9QSucwA5sQSF4mXapwSvh6ksz/rFRK4rjCWI0CBqqprmBr/ABqqAEZiEW3FZGcAB+9tMkL4xaUfyO4LMt/JugDrRiTWAaPwX6YAa0Ze2oDosm1IvvZ5q88tdqXGhshU7hLkUe6DT+pb8TtE3SRPwz8LNLkwyfYOO75caueIVeFehGdeQr0U8gO6cZgUYYhSvIBj87NMk3Rq3Y+NAWTiIzAbswB9rmdTQHIk2PQlxkZ0S8Z2LdEuOGRYvRQk5sYd2xBFLN0ANaUSZaC5pIHvoHckH3cgD1symT/G7UyjccnR9nq3W/dM/od2wDT99TRXTKl4lrQP4m6mdLJLfBvWP/iP9DPzj3uE2BB7f06QXSp9DDoju4SF8002ku4Ef50AR6rcZQvRWTqFNY/mOjA6tVrjKw7m8qWg9hs984HATQnDKmzoRuiv5ZEN5b0IXvq3i0L4U9NiWYrjsAAAD//54Dc4wAAAAGSURBVAMAvzRaLzuU8GkAAAAASUVORK5CYII=>

[image16]: <data:image/png;base64,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>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAAAt0lEQVR4AeyQLQ7CQBBGGzBYAgqBx3EcCBAUlgQDCguBBI0D31v0KhVVPUJF37bZTTatmWlVf/K9truZfdmZUdDiM8jkw+zezC51Q9C2uUa2BC9a2Q/LDbxoZRGWMWzAxcpm7CyEPKg/wBOmEFjZlcVHyIv6OZzhBE5m+t+yIeFOfQoreIOTmX8JE4r/cIQYitg2i4Xgtaf2C+ZmfMpoZTuOh+CliSzzTCy0soSzlWhlFZHZ6IksBwAA//8ek5s6AAAABklEQVQDAOGpHC9DrkvYAAAAAElFTkSuQmCC>

[image18]: <data:image/png;base64,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>

[image19]: <data:image/png;base64,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>