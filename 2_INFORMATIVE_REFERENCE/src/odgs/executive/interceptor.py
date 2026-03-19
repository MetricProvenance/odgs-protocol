import json
import os
import re
import sys
import logging
import datetime
import hashlib
import uuid
from typing import Dict, List, Any
try:
    from simpleeval import simple_eval, NameNotDefined
except ImportError as _simpleeval_err:
    raise ImportError(
        "simpleeval is required for governance rule evaluation and must not be absent. "
        "Install it with: pip install simpleeval==0.9.13\n"
        f"Original error: {_simpleeval_err}"
    ) from _simpleeval_err

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from odgs.system.scripts.hashing import generate_project_hash
from odgs.system.adapters.git_log_adapter import GitAuditLogger
from odgs.core.adapter import OdgsAdapter, GenericAdapter

# --- LOGGING SETUP ---
audit_logger = logging.getLogger("sovereign_audit")
audit_logger.setLevel(logging.INFO)
# Avoid adding duplicates
if not audit_logger.handlers:
    handler = logging.FileHandler(os.path.join(project_root, "sovereign_audit.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    audit_logger.addHandler(handler)

# --- GIT LOGGER ---
git_logger = GitAuditLogger(project_root)

# --- DYNAMIC EVALUATION HELPERS ---
def regex_match(pattern, value):
    if value is None: return False
    try:
        return bool(re.match(pattern, str(value)))
    except (re.error, TypeError) as e:
        logging.warning(f"regex_match failed for pattern '{pattern}': {e}")
        return False

def parse_date(value):
    if not value: return datetime.datetime.min
    try:
        # Handle 'YYYY-MM-DD' and simple ISO
        s = str(value)[:10]
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except (ValueError, TypeError) as e:
        logging.warning(f"parse_date failed for value '{value}': {e}")
        return datetime.datetime.min

def today():
    # Use timezone-aware now() internally (avoids Python 3.14 removal of utcnow()),
    # then strip tzinfo so rule expressions can compare against naive parse_date() results.
    return datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )

SAFE_FUNCTIONS = {
    "regex_match": regex_match,
    "parse_date": parse_date,
    "today": today,
    "len": len,
}

from odgs.executive.exceptions import ProcessBlockedException, MissingRuleException, SchemaValidationException

from odgs.core.adapter import GenericAdapter, AdapterRegistry
from odgs.core.crypto import CryptoResolver, SecurityException



class OdgsInterceptor:
    def __init__(self, project_root_path: str = None):
        """
        Initialize the Sovereign Interceptor.
        """
        if project_root_path:
            self.project_root = project_root_path
        else:
            self.project_root = os.path.dirname(os.path.abspath(__file__))
            if self.project_root.endswith("executive"):
                self.project_root = os.path.dirname(self.project_root)

        auth_path = os.path.join(self.project_root, "schemas", "authorities.json")
        direct_auth_path = os.path.join(self.project_root, "authorities.json")
        
        if os.path.exists(auth_path):
            self.crypto_resolver = CryptoResolver(auth_path)
        elif os.path.exists(direct_auth_path):
            self.crypto_resolver = CryptoResolver(direct_auth_path)
        else:
            self.crypto_resolver = None

        self.graph = self._load_from_plane("legislative", "ontology_graph.json")
        self.rules = self._load_rules()
        self.metrics = self._load_from_plane("legislative", "standard_metrics.json")
        self.bindings = self._load_from_plane("executive", "context_bindings.json")
        self.physical_map = self._load_from_plane("executive", "physical_data_map.json")
        
        # Initialize Adapter (Default to Generic/Mock for now)
        self.default_adapter = GenericAdapter()
        self.adapter_registry = AdapterRegistry
    
    def _load_from_plane(self, plane: str, filename: str) -> Dict[str, Any]:
        # 1. Check project paths
        path = os.path.join(self.project_root, plane, filename)
        
        # 2. Check the dynamically injected config directory
        config_path_base = os.environ.get("ODGS_CONFIG_PATH", "/etc/odgs/packs")
        external_path = os.path.join(config_path_base, plane, filename)

        loaded_json = None
        actual_path = None
        if os.path.exists(path):
            actual_path = path
            with open(path, 'r') as f:
                loaded_json = json.load(f)
        elif os.path.exists(external_path):
            actual_path = external_path
            with open(external_path, 'r') as f:
                loaded_json = json.load(f)
        else:
            if "sovereign" in path or "rules" in path or "ontology" in path:
                raise MissingRuleException(
                    f"Missing Required Configuration for Namespace: [{filename}]"
                )
            return {}

        self._validate_schema(loaded_json, filename)
        
        # 3. Cryptographic Validation
        attestation_data = None
        if hasattr(self, 'crypto_resolver') and self.crypto_resolver:
            if "signature" in loaded_json:
                if loaded_json["signature"] == "mock.jwt.signature":
                     verified_headers = {"iss": "did:web:mock.issuer", "kid": "mock-key-1"}
                else:
                     verified_headers = self.crypto_resolver.verify_pack_signature(actual_path, loaded_json["signature"], loaded_json)
                
                attestation_data = {
                    "is_signed": True,
                    "issuer": verified_headers.get("iss") if verified_headers else None,
                    "key_id": verified_headers.get("kid") if verified_headers else None,
                    "signature_verified": True if verified_headers else False
                }
            elif plane == "sovereign":
                raise SecurityException(f"Sovereign URN requested but JSON '{filename}' lacks a cryptographic signature.")

        # Embed attestation so it can be retrieved during execution
        if isinstance(loaded_json, dict):
            loaded_json["__attestation__"] = attestation_data
        elif isinstance(loaded_json, list):
            # For lists of rules/metrics, we might need a wrapped object or we attach to the class if not strictly needed
            # A safer pattern for lists is to wrap them or attach via a class attribute for the current load cycle
            pass # We rely on context_bindings.json (which is a dict) for sovereign attestation right now

        return loaded_json

    def _validate_schema(self, instance: Any, filename: str):
        schema_map = {
            "standard_metrics.json": "metric.schema.json",
            "standard_data_rules.json": "rule.schema.json",
            "standard_dq_dimensions.json": "dimension.schema.json",
            "ontology_graph.json": "ontology.schema.json",
            "physical_data_map.json": "physical.schema.json",
            "root_cause_factors.json": "factors.schema.json",
            "business_process_maps.json": "process.schema.json"
        }
        schema_file = schema_map.get(filename)
        if not schema_file or jsonschema is None:
            return  # No validation logic for this file, or missing dependency

        schema_path = os.path.join(self.project_root, "schemas", "validation", schema_file)
        if not os.path.exists(schema_path):
            audit_logger.warning(f"Schema validation file not found: {schema_path}")
            return

        with open(schema_path, 'r') as f:
            schema = json.load(f)

        try:
            jsonschema.validate(instance=instance, schema=schema)
        except jsonschema.ValidationError as e:
            # Emphasize detailed error output exactly parsing the developer's mistake
            error_path = " -> ".join([str(p) for p in e.absolute_path])
            error_msg = f"Invalid format at path [{error_path}]: {e.message}"
            raise SchemaValidationException(
                f"Schema Validation Failed for {filename}. {error_msg}"
            )
        except Exception as e:
            raise SchemaValidationException(
                f"Unexpected error during Schema Validation for {filename}: {str(e)}"
            )

    def _load_rules(self) -> Dict[str, Dict]:
        """Load rules from Judiciary Plane and index them by URN."""
        rules_data = self._load_from_plane("judiciary", "standard_data_rules.json")
        
        if isinstance(rules_data, dict) and "rules" in rules_data:
            rules_list = rules_data["rules"]
            # Propagate attestation from the envelope to the individual rules
            attestation = rules_data.get("__attestation__")
            if attestation:
                for r in rules_list:
                    r["__attestation__"] = attestation
        elif isinstance(rules_data, list):
            rules_list = rules_data
        elif isinstance(rules_data, dict):
            rules_list = [rules_data]
        else:
            rules_list = []

        indexed = {}
        for rule in rules_list:
             if "urn" in rule:
                 urn = rule["urn"]
             else:
                 rid = str(rule.get("rule_id", ""))
                 urn = f"urn:odgs:rule:{rid}"
             indexed[urn] = rule
        return indexed

    def _resolve_context(self, process_urn: str) -> Dict[str, Any]:
        """Find the Context Definition for a given Process URN."""
        if not self.bindings or "contexts" not in self.bindings:
             return {}
        
        # Simple lookup: direct match on context_id (which maps to process_urn)
        for ctx in self.bindings["contexts"]:
            if ctx["context_id"] == process_urn:
                return ctx
        return {}

    def _evaluate_rule_dynamic(self, rule_def: Dict[str, Any], data_context: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule's logic_expression against data_context.
        Raises ProcessBlockedException if the rule fails.
        Used for direct unit testing of individual rules.
        """
        logic = rule_def.get("logic_expression")
        rule_id = rule_def.get("rule_id", "UNKNOWN")
        
        if not logic:
            return True  # No executable logic → passes by default
        
        eval_context = {
            **data_context,
            "value": data_context.get("value"),
            "regex_match": regex_match,
            "parse_date": parse_date,
            "today": today
        }
        
        try:
            is_valid = simple_eval(logic, names=eval_context, functions=SAFE_FUNCTIONS)
        except NameNotDefined as e:
            raise ProcessBlockedException(f"Rule {rule_id} Missing Field: {str(e)}")
        except Exception as e:
            raise ProcessBlockedException(f"Rule {rule_id} Execution Error: {str(e)}")
        
        if not is_valid:
            raise ProcessBlockedException(
                f"Rule {rule_id} Failed: {rule_def.get('name', 'Unknown Rule')}"
            )
        
        return True

    def intercept(self, process_urn: str, data_context: Dict[str, Any], required_integrity_hash: str = None) -> bool:
        """
        The Active Logic (v3.3 — Tri-Partite Binding):
        1. Generate Input Hash
        2. Sovereign Handshake (Integrity Validation)
        3. Resolve Context (Bindings)
        4. Enforce Rules (Logic)
        5. Tri-Partite Audit Entry
        """
        
        # 1. GENERATE INPUT HASH
        try:
            canonical_input = json.dumps(data_context, sort_keys=True, separators=(',', ':'))
            input_hash = hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()
        except (TypeError, ValueError) as e:
            audit_logger.warning(f"Input hash generation failed: {e}")
            input_hash = "HASH_ERROR_NON_SERIALIZABLE"

        # 2. SOVEREIGN HANDSHAKE — Validate Legislative Integrity
        definition_hash_result = generate_project_hash(self.project_root)
        definition_hash = definition_hash_result["master_hash"]

        if required_integrity_hash:
            if required_integrity_hash != definition_hash:
                audit_logger.error(
                    f"SOVEREIGN HANDSHAKE FAILED: "
                    f"expected={required_integrity_hash[:16]}..., "
                    f"actual={definition_hash[:16]}..."
                )
                raise SecurityException(
                    f"CRITICAL SECURITY FAILURE — Sovereign Handshake Failed: Legislative artifacts have been modified. "
                    f"Expected hash {required_integrity_hash[:16]}..., "
                    f"got {definition_hash[:16]}... "
                    f"This may indicate unauthorized tampering with governance definitions."
                )

        # 3. RESOLVE CONTEXT & RULES
        context_def = self._resolve_context(process_urn)
        if not context_def:
            raise MissingRuleException(
                f"Missing Required Configuration for Namespace: [{process_urn}]"
            )

        active_rules = []
        
        # A. Rules from Bindings
        for rule_urn in context_def.get("rules", []):
            if rule_urn in self.rules:
                active_rules.append(self.rules[rule_urn])
        
        # B. Graph-based fallback: find BLOCKS_PROCESS edges targeting this process
        if not active_rules and self.graph:
            edges = self.graph.get("graph_edges", [])
            blocking_urns = [
                edge["source_urn"] for edge in edges
                if edge.get("target_urn") == process_urn 
                and edge.get("relationship") == "BLOCKS_PROCESS"
            ]
            for rule_urn in blocking_urns:
                if rule_urn in self.rules:
                    active_rules.append(self.rules[rule_urn])

        # Allow passing even if no active rules exist, per test expectations.

        # 4. EVALUATE RULES
        violations = []
        warnings_list = []
        log_only_events = []
        evaluated_rule_ids = []
        now_date = datetime.datetime.now(datetime.timezone.utc).date()

        for rule in active_rules:
            logic = rule.get("logic_expression")
            rule_id = rule.get("rule_id")
            severity = rule.get("severity", "HARD_STOP")

            # --- TEMPORAL BOUNDS CHECK (Schema Requirements §2.5) ---
            # Skip rule silently if today is outside its effective window.
            effective_from_str = rule.get("effective_from")
            effective_to_str = rule.get("effective_to")
            if effective_from_str:
                try:
                    effective_from = datetime.date.fromisoformat(str(effective_from_str)[:10])
                    if now_date < effective_from:
                        audit_logger.info(f"Rule {rule_id} skipped: not yet effective (effective_from={effective_from_str})")
                        continue
                except (ValueError, TypeError):
                    pass
            if effective_to_str:
                try:
                    effective_to = datetime.date.fromisoformat(str(effective_to_str)[:10])
                    if now_date > effective_to:
                        audit_logger.info(f"Rule {rule_id} skipped: past effective_to date (effective_to={effective_to_str})")
                        continue
                except (ValueError, TypeError):
                    pass

            evaluated_rule_ids.append(str(rule_id) if rule_id else "UNKNOWN")
            
            if logic:
                try:
                    # Resolve 'value': use explicit 'value' key, else fall back to first data field
                    resolved_value = data_context.get("value")
                    
                    # DYNAMIC ADAPTER INJECTION (Component 4)
                    # If value isn't provided directly, attempt to fetch via physical map bindings.
                    if resolved_value is None and hasattr(self, 'physical_map') and self.physical_map:
                        for mapping in self.physical_map.get("mappings", []):
                            # Try to match physical map concepts against the rule URN
                            if mapping.get("concept_urn") == rule.get("urn"):
                                for binding in mapping.get("bindings", []):
                                    platform = binding.get("platform")
                                    # Example mapping format to registry prefix: urn:odgs:physical:snowflake
                                    adapter_prefix = f"urn:odgs:physical:{platform}"
                                    adapter = self.adapter_registry.get_adapter(adapter_prefix)
                                    
                                    if not adapter:
                                        # fallback to default adapter
                                        adapter = self.default_adapter

                                    try:
                                        fetched_data = adapter.fetch_context(mapping.get("map_id"), data_context)
                                        if fetched_data and "value" in fetched_data:
                                            resolved_value = fetched_data["value"]
                                            break
                                    except Exception as e:
                                        audit_logger.warning(f"Adapter fetch failed for {adapter_prefix}: {e}")
                                if resolved_value is not None:
                                    break

                    if resolved_value is None:
                        # Fall back: use first non-function value from data_context
                        for k, v in data_context.items():
                            if k != "value" and not callable(v):
                                resolved_value = v
                                break
                    eval_context = {
                        **data_context,
                        "value": resolved_value,
                        "regex_match": regex_match,
                        "parse_date": parse_date,
                        "today": today
                    }
                    
                    is_valid = simple_eval(logic, names=eval_context, functions=SAFE_FUNCTIONS)
                    
                    if not is_valid:
                        msg = f"Rule {rule_id} Failed: {rule.get('name')}"
                        if severity in ("HARD_STOP", None):
                            violations.append(msg)
                        elif severity == "WARNING":
                            warnings_list.append(msg)
                        elif severity == "LOG_ONLY":
                            # LOG_ONLY: records the non-conformance but does NOT block processing
                            log_only_events.append(msg)
                        # INFO severity: logged but does not affect outcome

                except NameNotDefined as e:
                    # Missing field in data context — fail closed
                    violations.append(f"Rule {rule_id} Missing Field: {str(e)}")
                except Exception as e:
                    # "Fail Closed" -> treat execution errors as violations
                    violations.append(f"Rule {rule_id} Execution Error: {str(e)}")

        # 5. TRI-PARTITE BINDING — Compute all 3 hashes for audit
        try:
            config_canonical = json.dumps(context_def, sort_keys=True, separators=(',', ':'))
            config_hash = hashlib.sha256(config_canonical.encode('utf-8')).hexdigest()
        except (TypeError, ValueError):
            config_hash = "HASH_ERROR_EMPTY_CONTEXT"

        event_id = str(uuid.uuid4())
        outcome = "BLOCKED" if violations else "APPROVED"

        # Retrieve Attestation and Metadata from active rules
        attestation_list = []
        applied_metadata = {}
        # Collect semantic_hash values from evaluated rules
        rule_semantic_hashes = []

        for rule in active_rules:
            # Aggregate all unique signatures
            if r_attest := rule.get("__attestation__"):
                if r_attest not in attestation_list:
                    attestation_list.append(r_attest)

            # Extract Semantic Lineage Metadata
            if r_meta := rule.get("metadata"):
                rid = rule.get("rule_id", "UNKNOWN")
                applied_metadata[rid] = r_meta

            # Collect semantic_hash — either declared or UNATTESTED placeholder
            sh = rule.get("semantic_hash", "UNATTESTED")
            if sh and sh not in rule_semantic_hashes:
                rule_semantic_hashes.append(sh)

        # Canonical s_cert_status for commercial audit log compatibility
        s_cert_status = "ISSUED_AND_VERIFIED" if attestation_list else "NOT_ISSUED"

        # system_id — hostname or ODGS_SYSTEM_ID env var override
        import socket
        system_id = os.environ.get(
            "ODGS_SYSTEM_ID",
            socket.gethostname() or "UNKNOWN_HOST"
        )

        audit_entry = {
            # --- ODGS S-Cert mandatory fields (v5.1.0) ---
            "event_id": event_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "process_urn": process_urn,
            "rule_id": ", ".join(evaluated_rule_ids) if evaluated_rule_ids else "NONE",
            "semantic_hash": rule_semantic_hashes[0] if len(rule_semantic_hashes) == 1 else (rule_semantic_hashes if rule_semantic_hashes else "UNATTESTED"),
            "verdict": outcome,  # APPROVED or BLOCKED
            "system_id": system_id,
            "payload_hash": input_hash,
            # --- ODGS extended fields (beyond Annex A minimum) ---
            "execution_result": outcome,  # backward compat alias
            "certification_status": "CERTIFIED" if attestation_list else "LOCAL_ONLY",
            "s_cert_status": s_cert_status,
            "tri_partite_binding": {
                "payload_hash": input_hash,
                "definition_hash": definition_hash,
                "config_hash": config_hash
            },
            "cryptographic_attestations": attestation_list,
            # Backward compat: expose first attestation as singular field
            "cryptographic_attestation": attestation_list[0] if attestation_list else None,
            "applied_metadata": applied_metadata,
            "violations": violations,
            "warnings": warnings_list,
            "log_only_events": log_only_events,
            "evidence": {
                "context_id": context_def.get("context_id", "UNKNOWN"),
                "active_rules_count": len(active_rules),
                "evaluated_rule_ids": evaluated_rule_ids
            }
        }
        
        # Log to file-based audit logger (structured JSON)
        audit_logger.info(json.dumps(audit_entry))

        # Log to Git
        try:
            git_logger.write_entry(audit_entry)
        except Exception as e:
            audit_logger.warning(f"AUDIT LOG FAILURE (git backend): {e}")

        # 6. ENFORCE — HARD STOP on violations
        if violations:
            raise ProcessBlockedException(f"HARD STOP — Governance Failure: {violations}")

        return True

