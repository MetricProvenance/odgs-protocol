import json
import os
import re
import sys
import logging
import datetime
from typing import Dict, List, Any

# Add project root to sys.path to allow imports from odgs.system
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from odgs.system.scripts.hashing import generate_project_hash

# --- ARTICLE 12: IMMUTABLE AUDIT LOGGING ---
# In a real Sovereign Cloud, this would write to a WORM (Write Once Read Many) drive.
# Here we simulate it with a standard file logger.
audit_logger = logging.getLogger("sovereign_audit")
audit_logger.setLevel(logging.INFO)
# Ensure we don't add multiple handlers on reload
if not audit_logger.handlers:
    handler = logging.FileHandler(os.path.join(project_root, "sovereign_audit.log"))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    audit_logger.addHandler(handler)
# -------------------------------------------

class ProcessBlockedException(Exception):
    """Raised when a Process is blocked by a Rule Violation (Hard Stop)."""
    pass

class SecurityException(Exception):
    """Raised when a Cryptographic Handshake failure occurs."""
    pass

class OdgsInterceptor:
    def __init__(self, project_root_path: str = None):
        """
        Initialize the Interceptor.
        :param project_root_path: Path to the project root. 
                                  If None, attempts to find it relative to this file.
        """
        if project_root_path:
            self.project_root = project_root_path
        else:
            # We are in /executive/interceptor.py, so root is one level up
            self.project_root = os.path.dirname(os.path.abspath(__file__))
            if self.project_root.endswith("executive"):
                self.project_root = os.path.dirname(self.project_root)

        self.graph = self._load_from_plane("legislative", "ontology_graph.json")
        self.rules = self._load_rules()
        self.metrics = self._load_from_plane("legislative", "standard_metrics.json")
    
    def _load_from_plane(self, plane: str, filename: str) -> Dict:
        """
        Load JSON artifacts from their specific Sovereign Plane.
        """
        path = os.path.join(self.project_root, plane, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Sovereign Artifact not found in {plane} plane: {path}")
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

    def intercept(self, process_urn: str, data_context: Dict[str, Any], required_integrity_hash: str) -> bool:
        """
        The Core Logic: Checks if the requested Process Stage is blocked by any Rules.
        
        STRICT MODE ENFORCED:
        - required_integrity_hash is MANDATORY.
        - All decisions are logged to sovereign_audit.log.
        """
        
        # 1. ARTICLE 12 LOGGING (Start)
        audit_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "process_urn": process_urn,
            "input_hash": required_integrity_hash,
            "status": "PENDING"
        }

        print(f"🛡️  Interceptor Active: Checking Access for Process [{process_urn}]")

        try:
            # 2. SOVEREIGN HANDSHAKE (Cryptographic Verification)
            # This is now MANDATORY. The "Doorman" checks ID every time.
            print(f"   🔐 Handshake Requested. Verifying Integrity...")
            current_state = generate_project_hash(self.project_root)
            current_hash = current_state["master_hash"]
            
            if current_hash != required_integrity_hash:
                audit_entry["status"] = "REJECTED_HASH_MISMATCH"
                audit_entry["actual_hash"] = current_hash
                audit_logger.error(json.dumps(audit_entry))
                
                error_msg = (
                    f"CRITICAL SECURITY FAILURE: Governance Hash Mismatch.\n"
                    f"Expected: {required_integrity_hash}\n"
                    f"Actual:   {current_hash}\n"
                    f"The Semantic Laws have been altered or do not match the signature."
                )
                print(f"   ⛔ {error_msg}")
                raise SecurityException(error_msg)
            else:
                print(f"   ✅ Integrity Verified. Hash matches.")

            # 3. IDENTIFY BLOCKING RULES
            blocking_rules = self._find_blocking_rules(process_urn)
            
            if not blocking_rules:
                print("   ✅ No Hard Stop rules found for this process.")
                audit_entry["status"] = "APPROVED_NO_RULES"
                audit_logger.info(json.dumps(audit_entry))
                return True

            print(f"   ⚠️  Found {len(blocking_rules)} Potential Blocking Rules.")

            # 4. EVALUATE BLOCKING RULES
            for rule_urn in blocking_rules:
                rule_def = self.rules.get(rule_urn)
                if not rule_def:
                    print(f"   [warn] Rule definition not found for {rule_urn}, skipping.")
                    continue
                
                self._evaluate_rule(rule_def, data_context)
            
            print("   ✅ All Blocking Rules Passed. Access Granted.")
            audit_entry["status"] = "APPROVED"
            audit_logger.info(json.dumps(audit_entry))
            return True

        except Exception as e:
            # Catch Validation Errors and Log them as Rejections
            if audit_entry["status"] == "PENDING":
                 audit_entry["status"] = "REJECTED_RULE_VIOLATION"
            
            audit_entry["error_type"] = type(e).__name__
            audit_entry["error_msg"] = str(e)
            audit_logger.error(json.dumps(audit_entry))
            raise e

    def _find_blocking_rules(self, target_process_urn: str) -> List[str]:
        blockers = []
        edges = self.graph.get("graph_edges", [])
        for edge in edges:
            if (edge.get("target_urn") == target_process_urn and 
                edge.get("relationship") == "BLOCKS_PROCESS"):
                blockers.append(edge.get("source_urn"))
        return blockers

    def _evaluate_rule(self, rule_def: Dict, data: Dict):
        rule_id = rule_def.get("rule_id")
        rule_name = rule_def.get("name")
        print(f"      🔎 Verifying Rule {rule_id}: {rule_name}")

        # Logic for Rule 2021: ISO 6346 Container ID
        if str(rule_id) == "2021":
            cid = data.get("container_id", "")
            pattern = r"^[A-Z]{4}[0-9]{7}$"
            if not re.match(pattern, str(cid)):
                raise ProcessBlockedException(
                    f"HARD STOP: Rule {rule_id} Failed. "
                    f"Value '{cid}' does not match pattern {pattern}. "
                    f"Process is BLOCKED."
                )
        else:
             print(f"      [info] No executable logic implemented for Rule {rule_id}, passing by default.")

