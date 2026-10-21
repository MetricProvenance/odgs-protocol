# Gaia-X Integration (`ODRL-VC Profile` & `Data Transfer Agent`)

## 1. Bridging Phase 5 (Transfer) and Phase 6 (In-Pipeline Usage)

Within the **Gaia-X Architecture Document (`25.11`)** and the **Gaia-X Data Transfer Agent (`DTA`)**:

- **Phase 5 (Transfer):** The `DTA` evaluates pre-transfer access prerequisites (`odrl:read`) and records negotiated post-transfer consumer obligations on the `TransferRequestResult`.
- **Phase 6 (Access & Usage):** Because a transfer agent's involvement ends when bytes land at the consumer boundary, post-transfer obligations (`odrl:Duty`, `odrl:Prohibition`, such as *k*-anonymity aggregation or trade-secret filtering) must be enforced inside the consumer's processing pipeline, and the consumer must provide cryptographic proof of implemented policy enforcement (**Gaia-X Architecture Document 25.11**, §4.8.4.2).

## 2. Verification Workflow (`dta_verifier.py`)

1. **Bind Agreement (`bind_odrl_policy`):** The consumer binds the negotiated W3C ODRL 2.2 / Gaia-X ODRL-VC agreement (`uid`) to its target `process_urn`, setting `correlation_id` to the DTA `agreement_id` / `transfer_id`.
2. **Runtime Gate (`DataspaceRuntimePEP.evaluate`):** On every pipeline execution, the PEP evaluates the bound constraint against the payload and emits an `S-Cert` (`payload_hash` + `semantic_hash` + `correlation_id`).
3. **Cryptographic Attestation (`sign_s_cert_ed25519`):** The `S-Cert` is signed using Ed25519 (RFC 7515 JWS / `EdDSA`).
4. **Provider / DTA Verification (`verify_dta_post_transfer_obligation`):** The provider or DTA `CredentialVerification` plugin verifies the `correlation_id`, `semantic_hash`, `verdict == PASS`, and Ed25519 JWS signature without ever accessing the consumer's raw data.
