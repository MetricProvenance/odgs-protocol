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
                    if "input_payload_hash" in line:
                        found = True
                        print(f"  ✅ Log Entry Found: {line.strip()[:100]}...")
                        break
            self.assertTrue(found, "Did not find expected audit log entry with payload hash")

if __name__ == '__main__':
    unittest.main()
