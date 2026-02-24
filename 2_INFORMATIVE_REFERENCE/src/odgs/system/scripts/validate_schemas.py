#!/usr/bin/env python3
"""
ODGS Schema Validator — validates core JSON files against their meta-schemas.
Usage: python3 -m src.odgs.system.scripts.validate_schemas [--root <path>]
"""
import json
import os
import sys
from typing import List, Tuple

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def validate_array_against_schema(
    data_path: str,
    schema_path: str,
    item_label: str = "item"
) -> Tuple[int, int, List[str]]:
    """
    Validates each item in a JSON array file against a JSON Schema.
    Returns (passed, failed, errors).
    """
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        return (0, 1, [f"{data_path}: Expected array, got {type(data).__name__}"])
    
    validator = Draft7Validator(schema)
    passed = 0
    failed = 0
    errors = []
    
    for i, item in enumerate(data):
        errs = list(validator.iter_errors(item))
        if errs:
            failed += 1
            for err in errs:
                item_id = item.get("urn") or item.get("metric_id") or item.get("rule_id") or f"#{i}"
                errors.append(f"  {item_label} {item_id}: {err.message}")
        else:
            passed += 1
    
    return (passed, failed, errors)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    # Navigate from scripts/ to project root
    if "scripts" in root:
        root = os.path.join(root, "..", "..", "..", "..")
    root = os.path.normpath(root)
    
    schemas_dir = os.path.join(root, "1_NORMATIVE_SPECIFICATION", "schemas")
    meta_dir = os.path.join(schemas_dir, "meta")
    
    validations = [
        (
            os.path.join(schemas_dir, "legislative", "standard_metrics.json"),
            os.path.join(meta_dir, "metric.schema.json"),
            "Metric"
        ),
        (
            os.path.join(schemas_dir, "judiciary", "standard_data_rules.json"),
            os.path.join(meta_dir, "rule.schema.json"),
            "Rule"
        ),
    ]
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    print("=" * 60)
    print("ODGS Schema Validation Report")
    print("=" * 60)
    
    for data_path, schema_path, label in validations:
        if not os.path.exists(data_path):
            print(f"\n⚠️  SKIP: {data_path} not found")
            continue
        if not os.path.exists(schema_path):
            print(f"\n⚠️  SKIP: {schema_path} not found")
            continue
        
        passed, failed, errors = validate_array_against_schema(data_path, schema_path, label)
        total_passed += passed
        total_failed += failed
        all_errors.extend(errors)
        
        status = "✅" if failed == 0 else "❌"
        print(f"\n{status} {label}s: {passed} passed, {failed} failed")
        for err in errors[:5]:  # Show first 5 errors per category
            print(err)
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
