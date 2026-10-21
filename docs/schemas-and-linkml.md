# LinkML Vocabulary, OWL 2 Ontology & Normative JSON Schemas

This repository ships machine-readable vocabulary and schema artefacts aligned with **ISO/IEC 38505-1:2026**, **ISO/IEC 25012:2008**, the **Eclipse Dataspace Working Group (`linkml/cap.yaml`)**, and **Gaia-X (`odrl-vc-profile`)**:

1. **W3C OWL 2 Ontology (`1_NORMATIVE_SPECIFICATION/ontology/ontology_graph.owl`):**
   - Formalises the 5-Plane Constitutional Stack (`SovereignDefinition`, `Dimension`, `Rule`, `Metric`, `Process`, `ContextBinding`, `SemanticCertificate`) grounded in `ISO/IEC 38505-1:2026`, `ISO/IEC 25012:2008`, `W3C ODRL 2.2`, and `W3C PROV-O`.
2. **LinkML Dataspace Ontology (`1_NORMATIVE_SPECIFICATION/ontology/odgs_dataspace.linkml.yaml`):**
   - Defines `AuthoritativeSource` (`exact_mappings: [cap:SpecifiedRequirement, prov:Plan]`), `ExecutableRule` (`close_mappings: [odrl:Rule, ovc:Constraint]`), `ProcessBinding`, and `SemanticCertificate` (`close_mappings: [cred:Evidence, prov:Entity]`).
3. **JSON-LD Context (`1_NORMATIVE_SPECIFICATION/schemas/odgs-dataspace.context.jsonld`):**
   - Maps `odgs:` properties directly to `odrl:`, `cred:`, `prov:`, `cap:`, and `ovc:` namespaces.
4. **Normative JSON Schemas (`1_NORMATIVE_SPECIFICATION/schemas/`):**
   - `01-metrics-schema.json` & `legislative/standard_dq_dimensions.json`: 60 data quality dimensions mapped to `ISO/IEC 25012:2008` (`iso25012Characteristic`), `ISO 8000-8`, `ETSI EN 304 311`, and `ISO/IEC 38505-1:2026` (`iso38505GovernanceFacet`).
   - `02-rules-schema.json`: Deterministic validation rules (`HARD_STOP`, `SOFT_STOP`, `LOG_ONLY`).
   - `03-ontology-schema.json` & `executive/context_bindings.json`: Contextual process bindings (`ISO/IEC 38505-1:2026`).
   - `04-s-cert-schema.json`: Validates both **Level 1 (Core Conformance)** and **Level 2 (Attested Conformance)** `S-Cert` receipts, including `correlation_id`, `jws_signature`, `authority_id`, and `issuing_jwk_url`.
