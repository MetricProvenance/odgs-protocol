import argparse
import json
import os
import sys

# We import the validation logic from the odgs package
# Ensure PYTHONPATH is set correctly when running this
# Path to project root (parent of execution dir)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from odgs.scripts.validate_schema import validate_metric, validate_data_rule

def validate_and_feedback(path):
    report = {
        "status": "success",
        "issues": [],
        "file_status": {}
    }
    
    # Validate Metrics
    m_path = os.path.join(path, "standard_metrics.json")
    if os.path.exists(m_path):
        with open(m_path, 'r') as f:
            try:
                metrics = json.load(f)
                file_issues = []
                for m in metrics:
                    errs = validate_metric(m)
                    if errs:
                        file_issues.extend([f"Metric '{m.get('name')}' : {e}" for e in errs])
                
                if file_issues:
                    report["status"] = "error"
                    report["issues"].extend(file_issues)
                    report["file_status"]["standard_metrics.json"] = "invalid"
                else:
                    report["file_status"]["standard_metrics.json"] = "valid"

            except json.JSONDecodeError:
                report["status"] = "error"
                report["issues"].append(f"Invalid JSON format in {m_path}")
    else:
         report["issues"].append(f"Missing {m_path}")

    # Validate Rules
    r_path = os.path.join(path, "standard_data_rules.json")
    if os.path.exists(r_path):
        with open(r_path, 'r') as f:
            try:
                rules = json.load(f)
                file_issues = []
                for r in rules:
                    errs = validate_data_rule(r)
                    if errs:
                        file_issues.extend([f"Rule '{r.get('name')}' : {e}" for e in errs])
                
                if file_issues:
                    report["status"] = "error"
                    report["issues"].extend(file_issues)
                    report["file_status"]["standard_data_rules.json"] = "invalid"
                else:
                    report["file_status"]["standard_data_rules.json"] = "valid"
            except json.JSONDecodeError:
                report["status"] = "error"
                report["issues"].append(f"Invalid JSON format in {r_path}")
    
    # Output the structured report to STDOUT for the Agent to read
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    
    validate_and_feedback(args.path)
