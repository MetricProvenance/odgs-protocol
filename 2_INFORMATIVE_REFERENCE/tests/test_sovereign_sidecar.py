import unittest
import os
import shutil
import json
import logging
import sys
import re

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Force path to src for odgs import if necessary
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException
except ImportError:
    # Try src.odgs
    from src.odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException

class TestSovereignSidecar(unittest.TestCase):
    
    def setUp(self):
        # Point to src/odgs where the planes live
        self.interceptor = OdgsInterceptor(os.path.join(project_root, "src", "odgs"))
        self.test_urn = "urn:odgs:process:test_transaction"
        
    def test_dynamic_01_positive_numeric(self):
        # Rule 2007: value > 0
        print("\nTesting Positive Numeric (Rule 2007)...")
        rule_def = {
            "rule_id": "2007",
            "name": "Test Positive",
            "logic_expression": "value > 0"
        }
        
        # Valid Case
        try:
            self.interceptor._evaluate_rule_dynamic(rule_def, {"value": 100})
            print("  ✅ Rule 2007 passed for 100")
        except ProcessBlockedException:
            self.fail("Rule 2007 should have passed for 100")
            
        # Invalid Case
        try:
            self.interceptor._evaluate_rule_dynamic(rule_def, {"value": -5})
            self.fail("Rule 2007 should have failed for -5")
        except ProcessBlockedException:
             print("  ✅ Rule 2007 correctly blocked -5")

    def test_dynamic_02_percentage(self):
        print("\nTesting Percentage (Rule 2020)...")
        # Rule 2020: value >= 0 and value <= 100
        rule_def = {
            "rule_id": "2020",
            "name": "Test Percentage",
            "logic_expression": "value >= 0 and value <= 100"
        }
        
        self.interceptor._evaluate_rule_dynamic(rule_def, {"value": 50}) # Pass
        print("  ✅ 50% Passed")
        
        with self.assertRaises(ProcessBlockedException):
            self.interceptor._evaluate_rule_dynamic(rule_def, {"value": 150}) # Fail
        print("  ✅ 150% Blocked")

    def test_dynamic_03_regex_container(self):
         print("\nTesting Regex Container (Rule 2021)...")
         # Rule 2021: Regex match
         rule_def = {
             "rule_id": "2021",
             "name": "Test Container",
             "logic_expression": "regex_match(r'^[A-Z]{4}[0-9]{7}$', value)"
         }
         
         self.interceptor._evaluate_rule_dynamic(rule_def, {"value": "MSKU1234567"}) # Pass
         print("  ✅ Valid Container ID Passed")
         
         with self.assertRaises(ProcessBlockedException):
             self.interceptor._evaluate_rule_dynamic(rule_def, {"value": "INVALID"}) # Fail
         print("  ✅ Invalid Container ID Blocked")
         
    def test_dynamic_04_date_parsing(self):
        print("\nTesting Date Logic (Rule 2027)...")
        # Rule 2027: parse_date(value) <= today()
        rule_def = {
            "rule_id": "2027",
            "name": "Test Future Date",
            "logic_expression": "parse_date(value) <= today()"
        }
        
        self.interceptor._evaluate_rule_dynamic(rule_def, {"value": "2020-01-01"}) # Pass (Past)
        print("  ✅ Past Date Passed")
        
        future_date = "2099-01-01"
        with self.assertRaises(ProcessBlockedException):
             self.interceptor._evaluate_rule_dynamic(rule_def, {"value": future_date}) # Fail
        print("  ✅ Future Date Blocked")

    def test_audit_log_generation(self):
        print("\nTesting Audit Log Generation...")
        # Since we mock the graph or bypass it, intercept won't find blocking rules.
        # But logging should happen.
        
        data = {"test": "data", "value": 123}
        # Fake hash for integrity.
        # However, intercept checks integrity against REAL hash.
        # So we fetch real hash first.
        from odgs.system.scripts.hashing import generate_project_hash
        src_odgs_path = os.path.join(project_root, "src", "odgs")
        real_hash = generate_project_hash(src_odgs_path)["master_hash"]
        
        result = self.interceptor.intercept("urn:fake:process", data, required_integrity_hash=real_hash)
        self.assertTrue(result)
        
        # Log is at src/odgs because that's where Interceptor is initialized
        log_path = os.path.join(project_root, "src", "odgs", "sovereign_audit.log")
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
            found = False
            for line in reversed(lines):
                if "urn:fake:process" in line:
                    if "payload_hash" in line:
                        found = True
                        print(f"  ✅ Log Entry Found: {line.strip()[:100]}...")
                        break
            self.assertTrue(found, "Did not find expected audit log entry with payload hash")

    def test_dynamic_05_v4_1_0_features(self):
        print("\nTesting v4.1.0 Features (Array Attestations & Metadata)...")
        # Add Rules with metadata and attestations
        rule_1 = {
            "rule_id": "9001",
            "name": "Sovereign Rule",
            "logic_expression": "value == 'VALID'",
            "metadata": {"collibra_asset_id": "C-12345"},
            "__attestation__": {"is_signed": True, "key_id": "eu-ai-act-key"}
        }
        rule_2 = {
            "rule_id": "9002",
            "name": "Local Rule",
            "logic_expression": "len(value) > 3",
            "metadata": {"databricks_table": "gold_users"},
            "__attestation__": {"is_signed": True, "key_id": "local-enterprise-key"}
        }
        
        self.interceptor.rules["urn:odgs:rule:9001"] = rule_1
        self.interceptor.rules["urn:odgs:rule:9002"] = rule_2
        
        # Mock Context Resolution
        original_resolve = self.interceptor._resolve_context
        self.interceptor._resolve_context = lambda urn: {
            "context_id": urn,
            "rules": ["urn:odgs:rule:9001", "urn:odgs:rule:9002"]
        }
        
        from odgs.system.scripts.hashing import generate_project_hash
        src_odgs_path = os.path.join(project_root, "src", "odgs")
        real_hash = generate_project_hash(src_odgs_path)["master_hash"]
        
        # Process Pass
        test_urn = "urn:fake:process_v4_1_0"
        self.interceptor.intercept(test_urn, {"value": "VALID"}, required_integrity_hash=real_hash)
        
        log_path = os.path.join(project_root, "src", "odgs", "sovereign_audit.log")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            found = False
            for line in reversed(lines):
                if test_urn in line:
                    json_str = line.split(" - ", 1)[1]
                    entry = json.loads(json_str)
                    # v4.1.0 Assertions
                    self.assertIn("cryptographic_attestations", entry, "Missing multi-sign array")
                    self.assertEqual(len(entry["cryptographic_attestations"]), 2, "Should aggregate exactly 2 signatures")
                    self.assertIn("applied_metadata", entry, "Missing applied_metadata lineage object")
                    self.assertEqual(entry["applied_metadata"]["9001"]["collibra_asset_id"], "C-12345")
                    self.assertEqual(entry["applied_metadata"]["9002"]["databricks_table"], "gold_users")
                    found = True
                    print(f"  ✅ v4.1.0 Multi-Sign & Metadata correctly tracked in Audit Log.")
                    break
                    
            self.assertTrue(found, "v4.1.0 Audit Log entry not found.")
        
        # Restore mock
        self.interceptor._resolve_context = original_resolve


if __name__ == '__main__':
    unittest.main()
