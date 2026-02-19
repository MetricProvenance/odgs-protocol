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
    return datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

SAFE_FUNCTIONS = {
    "regex_match": regex_match,
    "parse_date": parse_date,
    "today": today,
    "len": len,
}

class ProcessBlockedException(Exception):
    """Raised when a Process is blocked by a Rule Violation (Hard Stop)."""
    pass

class SecurityException(Exception):
    """Raised when a Cryptographic Handshake failure occurs."""
    pass

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

        self.graph = self._load_from_plane("legislative", "ontology_graph.json")
        self.rules = self._load_rules()
        self.metrics = self._load_from_plane("legislative", "standard_metrics.json")
        self.bindings = self._load_from_plane("executive", "context_bindings.json")
        
        # Initialize Adapter (Default to Generic/Mock for now)
        self.adapter = GenericAdapter()
    
    def _load_from_plane(self, plane: str, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.project_root, plane, filename)
        if not os.path.exists(path):
            # In a real scenario, this might crash, but for resilience we log error
            print(f"CRITICAL: Sovereign Artifact missing: {path}")
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    def _load_rules(self) -> Dict[str, Dict]:
        """Load rules from Judiciary Plane and index them by URN."""
        rules_data = self._load_from_plane("judiciary", "standard_data_rules.json")
        
        if isinstance(rules_data, dict) and "rules" in rules_data:
            rules_list = rules_data["rules"]
        elif isinstance(rules_data, list):
            rules_list = rules_data
        elif isinstance(rules_data, dict):
            rules_list = [rules_data]
        else:
            rules_list = []

        indexed = {}
        for rule in rules_list:
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
        active_rules = []
        
        # A. Rules from Bindings
        if context_def:
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

        # 4. EVALUATE RULES
        violations = []
        warnings_list = []
        
        for rule in active_rules:
            logic = rule.get("logic_expression")
            rule_id = rule.get("rule_id")
            severity = rule.get("severity", "HARD_STOP")
            
            if logic:
                try:
                    # Resolve 'value': use explicit 'value' key, else fall back to first data field
                    resolved_value = data_context.get("value")
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
                        if severity == "HARD_STOP":
                            violations.append(msg)
                        elif severity == "WARNING":
                            warnings_list.append(msg)
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
        
        audit_entry = {
            "event_id": event_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "process_urn": process_urn,
            "outcome": outcome,
            "violations": violations,
            "warnings": warnings_list,
            "evidence": {
                "input_payload_hash": input_hash,
                "definition_hash": definition_hash,
                "config_hash": config_hash,
                "tripartite_binding": f"{input_hash[:8]}:{definition_hash[:8]}:{config_hash[:8]}",
                "context_id": context_def.get("context_id", "UNKNOWN"),
                "active_rules_count": len(active_rules)
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

