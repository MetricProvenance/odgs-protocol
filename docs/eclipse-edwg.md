# Eclipse Dataspace Working Group Integration (`CAP v2.2.1`, `DRP`, `DSP`)

## 1. Complementarity with Eclipse CAP v2.2.1 (`dataspace-cap`)

The **Eclipse Conformity Assessment Policy and Credential Vocabulary (`CAP v2.2.1`, `https://w3id.org/eclipse-cap/v2.2.1/#`)** models standing organizational and service conformity credentials (`cap:Declaration`, `cap:Certification`, `cap:Accreditation`) as **W3C Verifiable Credentials v2.0**. By charter, CAP scopes out *"Automated compliance or Compliance as Code"* and *"The management of the policies, the claims and the evidence."*

`odgs-dataspace-bridge` supplies that runtime evidence layer:

| Eclipse CAP v2.2.1 Construct | ODGS Dataspace Bridge Counterpart | Integration Function |
| :--- | :--- | :--- |
| `cap:SpecifiedRequirement` | `AuthoritativeSource` & `ExecutableRule` (`semantic_hash`) | Binds the requirement URI to a SHA-256 digest of the verbatim statutory or rulebook text and a deterministic boolean expression. |
| `cap:ConformityAssessment` | `DataspaceRuntimePEP.evaluate()` | Executes deterministic runtime evaluation at the target `process_urn`. |
| `cred:Evidence` (`cred:id`, `cred:digest`) | `export_cap_cred_evidence(s_cert)` | Exports the zero-knowledge `S-Cert` as a `cred:Evidence` block with `cred:id = urn:uuid:{event_id}` and `cred:digest = sha256-{digest}`. |
| `cap:Declaration` / `cap:Certification` | `export_cap_declaration_vc(s_cert, ...)` | Packages the runtime `S-Cert` evidence directly inside a W3C VC v2.0 `cap:Declaration`. |

## 2. Complementarity with Eclipse DRP (`dataspace-drp`)

The **Eclipse Dataspace Rights Profile (`DRP`)** defines a `delegationEvidence` structure carrying `target.environment.licenses` and `Permit`/`Deny` rules, specifying that if licence conditions are not met, the `accessSubject` *"MUST not process the resource."*

`bind_drp_delegation_evidence()` compiles `delegationEvidence` into an ODGS `ExecutableRule` and `ProcessBinding` that triggers `HARD_STOP` (`AdministrativeRecusalError`) if required licences are absent at runtime.
