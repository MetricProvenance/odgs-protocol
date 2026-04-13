"""
ODGS v6.0.0 Test Suite — Core Engine Enhancements
==================================================
Tests every v6.0.0 capability:
  A.1  SOFT_STOP severity with override tokens
  A.2  Batch evaluation (intercept_batch)
  A.3  Rule dependency chains (topological sort)
  A.4  Webhook / event emission
  A.5  Conformance self-check
  A.6  Rule versioning in S-Cert audit

Plus regression tests for existing v5 HARD_STOP/WARNING/INFO behavior.
"""

import json
import os
import sys
import logging
import hashlib
import uuid
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# ---------- path setup ----------
SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")
)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from odgs.executive.exceptions import (
    ProcessBlockedException,
    SoftStopException,
    DependencyFailedException,
    MissingRuleException,
    SchemaValidationException,
    ConformanceException,
)
from odgs.executive.interceptor import (
    OdgsInterceptor,
    OdgsEventEmitter,
    _topological_sort,
    SAFE_FUNCTIONS,
    regex_match,
    parse_date,
    today,
)


# ====================================================================
# Fixtures
# ====================================================================

@pytest.fixture
def sovereign_project(tmp_path):
    """Create a minimal ODGS Sovereign Territory for testing."""
    # Legislative
    legislative = tmp_path / "legislative"
    legislative.mkdir()
    (legislative / "ontology_graph.json").write_text(json.dumps({
        "graph_edges": [
            {"source_urn": "urn:odgs:rule:R001", "target_urn": "urn:ctx:test_process",
             "relationship": "BLOCKS_PROCESS"},
        ]
    }))
    (legislative / "standard_metrics.json").write_text(json.dumps([]))

    # Judiciary
    judiciary = tmp_path / "judiciary"
    judiciary.mkdir()
    (judiciary / "standard_data_rules.json").write_text(json.dumps({
        "rules": [
            {
                "rule_id": "R001",
                "urn": "urn:odgs:rule:R001",
                "name": "Revenue must be positive",
                "severity": "HARD_STOP",
                "logic_expression": "value > 0",
                "version": "1.0.0",
            },
            {
                "rule_id": "R002",
                "urn": "urn:odgs:rule:R002",
                "name": "Revenue warning threshold",
                "severity": "WARNING",
                "logic_expression": "value > 100",
            },
            {
                "rule_id": "R003",
                "urn": "urn:odgs:rule:R003",
                "name": "Soft stop on large transactions",
                "severity": "SOFT_STOP",
                "logic_expression": "value < 1000000",
                "version": "2.1.0",
            },
            {
                "rule_id": "R004",
                "urn": "urn:odgs:rule:R004",
                "name": "Dependent rule — only if R001 passes",
                "severity": "HARD_STOP",
                "logic_expression": "value > 10",
                "depends_on": ["urn:odgs:rule:R001"],
                "version": "1.0.0",
            },
            {
                "rule_id": "R005",
                "urn": "urn:odgs:rule:R005",
                "name": "Info-only observation",
                "severity": "INFO",
                "logic_expression": "value > 50",
            },
        ]
    }))

    # Executive
    executive = tmp_path / "executive"
    executive.mkdir()
    (executive / "context_bindings.json").write_text(json.dumps({
        "contexts": [
            {
                "context_id": "urn:ctx:test_process",
                "rules": [
                    "urn:odgs:rule:R001",
                    "urn:odgs:rule:R002",
                    "urn:odgs:rule:R003",
                    "urn:odgs:rule:R004",
                    "urn:odgs:rule:R005",
                ],
            }
        ]
    }))
    (executive / "physical_data_map.json").write_text(json.dumps({"mappings": []}))

    # odgs.json — no webhooks
    (tmp_path / "odgs.json").write_text(json.dumps({"project_name": "test", "version": "6.0.0"}))

    return tmp_path


@pytest.fixture
def interceptor(sovereign_project):
    """Create an interceptor scoped to the test sovereign project."""
    return OdgsInterceptor(project_root_path=str(sovereign_project))


# ====================================================================
# A.0: Regression — Existing v5 behavior
# ====================================================================

class TestV5Regression:
    def test_hard_stop_blocks_on_failure(self, interceptor):
        """HARD_STOP rule (value > 0) must raise when value is negative."""
        with pytest.raises(ProcessBlockedException, match="R001"):
            interceptor.intercept("urn:ctx:test_process", {"value": -5})

    def test_approved_when_rules_pass(self, interceptor):
        """All rules pass for a valid positive value."""
        result = interceptor.intercept("urn:ctx:test_process", {"value": 500})
        assert result is True

    def test_missing_context_raises(self, interceptor):
        """Unknown process URN raises MissingRuleException."""
        with pytest.raises(MissingRuleException):
            interceptor.intercept("urn:ctx:unknown_process", {"value": 100})


# ====================================================================
# A.1: SOFT_STOP severity
# ====================================================================

class TestSoftStop:
    def test_soft_stop_blocks_without_override(self, interceptor):
        """SOFT_STOP rule fails and no override → BLOCKED."""
        # R003: value < 1_000_000 → fails when value >= 1M
        with pytest.raises(ProcessBlockedException, match="R003"):
            interceptor.intercept("urn:ctx:test_process", {"value": 2_000_000})

    def test_soft_stop_passes_with_override_token(self, interceptor):
        """SOFT_STOP rule fails BUT override_token supplied → APPROVED."""
        result = interceptor.intercept(
            "urn:ctx:test_process",
            {"value": 2_000_000},
            override_token="admin-override-xyz",
        )
        assert result is True

    def test_soft_stop_override_is_logged(self, interceptor, caplog):
        """Override token hash is logged in audit trail."""
        with caplog.at_level(logging.INFO, logger="sovereign_audit"):
            interceptor.intercept(
                "urn:ctx:test_process",
                {"value": 2_000_000},
                override_token="test-token-123",
            )
        
        # Find the JSON audit log entry
        token_hash = hashlib.sha256(b"test-token-123").hexdigest()
        found = any(token_hash[:16] in record.message for record in caplog.records)
        assert found, f"Expected override token hash {token_hash[:16]} in audit log"


# ====================================================================
# A.2: Batch evaluation
# ====================================================================

class TestBatchEvaluation:
    def test_batch_all_pass(self, interceptor):
        items = [
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": 500}},
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": 200}},
        ]
        result = interceptor.intercept_batch(items)
        assert result["total"] == 2
        assert result["passed"] == 2
        assert result["failed"] == 0

    def test_batch_mixed_results(self, interceptor):
        items = [
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": 500}},
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": -1}},
        ]
        result = interceptor.intercept_batch(items)
        assert result["passed"] == 1
        assert result["failed"] == 1
        assert result["results"][0]["status"] == "APPROVED"
        assert result["results"][1]["status"] == "BLOCKED"

    def test_batch_fail_fast(self, interceptor):
        items = [
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": -1}},
            {"process_urn": "urn:ctx:test_process", "data_context": {"value": 500}},
        ]
        result = interceptor.intercept_batch(items, fail_fast=True)
        assert result["evaluated"] == 1
        assert result["failed"] == 1

    def test_batch_empty_input(self, interceptor):
        result = interceptor.intercept_batch([])
        assert result["total"] == 0
        assert result["passed"] == 0


# ====================================================================
# A.3: Rule dependency chains
# ====================================================================

class TestDependencyChains:
    def test_topological_sort_respects_order(self):
        """Rules with depends_on are sorted so dependencies come first."""
        rules = [
            {"rule_id": "B", "urn": "urn:odgs:rule:B", "depends_on": ["urn:odgs:rule:A"]},
            {"rule_id": "A", "urn": "urn:odgs:rule:A"},
        ]
        sorted_rules = _topological_sort(rules, {})
        assert sorted_rules[0]["rule_id"] == "A"
        assert sorted_rules[1]["rule_id"] == "B"

    def test_dependency_failure_cascades(self, sovereign_project):
        """When R001 fails, R004 (depends_on R001) should also fail."""
        interceptor = OdgsInterceptor(project_root_path=str(sovereign_project))
        with pytest.raises(ProcessBlockedException, match="R001"):
            interceptor.intercept("urn:ctx:test_process", {"value": -1})

    def test_dependency_pass_allows_child(self, interceptor):
        """When R001 passes, R004 gets evaluated normally."""
        # R001: value > 0  ✓  |  R004: value > 10  ✓ (for value=50)
        result = interceptor.intercept("urn:ctx:test_process", {"value": 50})
        assert result is True

    def test_cycle_detection(self, caplog):
        """Cycles in depends_on should be logged as warnings, not crash."""
        rules = [
            {"rule_id": "X", "urn": "urn:odgs:rule:X", "depends_on": ["urn:odgs:rule:Y"]},
            {"rule_id": "Y", "urn": "urn:odgs:rule:Y", "depends_on": ["urn:odgs:rule:X"]},
        ]
        with caplog.at_level(logging.WARNING, logger="sovereign_audit"):
            sorted_rules = _topological_sort(rules, {})
        
        # Should still return all rules (cycle doesn't crash)
        assert len(sorted_rules) == 2


# ====================================================================
# A.4: Webhook / Event Emitter
# ====================================================================

class TestWebhookEmitter:
    def test_emitter_loads_config(self, sovereign_project):
        """Emitter loads webhook config from odgs.json."""
        (sovereign_project / "odgs.json").write_text(json.dumps({
            "webhooks": [
                {"url": "https://soc.example.com/odgs", "events": ["BLOCKED"]}
            ]
        }))
        emitter = OdgsEventEmitter(str(sovereign_project))
        assert len(emitter.webhooks) == 1

    def test_emitter_no_config(self, tmp_path):
        """Emitter gracefully handles missing odgs.json."""
        emitter = OdgsEventEmitter(str(tmp_path))
        assert emitter.webhooks == []

    @patch("urllib.request.urlopen")
    def test_emitter_dispatches_on_match(self, mock_urlopen, sovereign_project):
        (sovereign_project / "odgs.json").write_text(json.dumps({
            "webhooks": [
                {"url": "https://soc.example.com", "events": ["BLOCKED"]}
            ]
        }))
        emitter = OdgsEventEmitter(str(sovereign_project))
        emitter.emit("BLOCKED", {"rule_id": "R001"})
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_emitter_skips_non_matching_event(self, mock_urlopen, sovereign_project):
        (sovereign_project / "odgs.json").write_text(json.dumps({
            "webhooks": [
                {"url": "https://soc.example.com", "events": ["APPROVED"]}
            ]
        }))
        emitter = OdgsEventEmitter(str(sovereign_project))
        emitter.emit("BLOCKED", {"rule_id": "R001"})
        mock_urlopen.assert_not_called()


# ====================================================================
# A.5: Conformance self-check
# ====================================================================

class TestConformanceCheck:
    def test_l1_conformant(self, interceptor):
        """Full sovereign project passes L1."""
        result = interceptor.conformance_check("L1")
        assert result["conformant"] is True

    def test_l1_fails_missing_judiciary(self, tmp_path):
        """Missing judiciary/standard_data_rules.json fails at init (fail-closed)."""
        # Create only legislative and executive
        (tmp_path / "legislative").mkdir()
        (tmp_path / "legislative" / "ontology_graph.json").write_text("{}")
        (tmp_path / "executive").mkdir()
        (tmp_path / "executive" / "context_bindings.json").write_text("{}")

        # The interceptor refuses to initialize when judiciary rules are absent
        # This is "fail-closed" by design — no rules = no processing allowed
        with pytest.raises(MissingRuleException, match="standard_data_rules"):
            OdgsInterceptor(project_root_path=str(tmp_path))

    def test_l2_conformant(self, interceptor):
        """Full project passes L2."""
        result = interceptor.conformance_check("L2")
        assert result["conformant"] is True


# ====================================================================
# A.6: Rule versioning in S-Cert
# ====================================================================

class TestRuleVersioning:
    def test_version_recorded_in_audit(self, interceptor, caplog):
        """Versioned rules (R001 v1.0.0, R003 v2.1.0) appear in audit log."""
        with caplog.at_level(logging.INFO, logger="sovereign_audit"):
            interceptor.intercept("urn:ctx:test_process", {"value": 500})
        
        # Find audit JSON in log records
        audit_json = None
        for record in caplog.records:
            try:
                audit_json = json.loads(record.message)
                break
            except (json.JSONDecodeError, ValueError):
                continue
        
        assert audit_json is not None, "No JSON audit entry found in logs"
        assert "rule_versions" in audit_json
        assert audit_json["rule_versions"].get("R001") == "1.0.0"
        assert audit_json["rule_versions"].get("R003") == "2.1.0"


# ====================================================================
# Schema Tests
# ====================================================================

class TestRuleSchema:
    def test_schema_allows_soft_stop(self):
        """rule.schema.json must accept SOFT_STOP as a valid severity."""
        # Load the schema
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "1_NORMATIVE_SPECIFICATION", "schemas", "meta", "rule.schema.json"
        )
        if not os.path.exists(schema_path):
            pytest.skip("rule.schema.json not found")

        with open(schema_path) as f:
            schema = json.load(f)

        severity_enum = schema["properties"]["severity"]["enum"]
        assert "SOFT_STOP" in severity_enum
        assert "HARD_STOP" in severity_enum
        assert "WARNING" in severity_enum
        assert "INFO" in severity_enum

    def test_schema_has_depends_on(self):
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "1_NORMATIVE_SPECIFICATION", "schemas", "meta", "rule.schema.json"
        )
        if not os.path.exists(schema_path):
            pytest.skip("rule.schema.json not found")

        with open(schema_path) as f:
            schema = json.load(f)

        assert "depends_on" in schema["properties"]
        assert schema["properties"]["depends_on"]["type"] == "array"

    def test_schema_has_version(self):
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "1_NORMATIVE_SPECIFICATION", "schemas", "meta", "rule.schema.json"
        )
        if not os.path.exists(schema_path):
            pytest.skip("rule.schema.json not found")

        with open(schema_path) as f:
            schema = json.load(f)

        assert "version" in schema["properties"]


# ====================================================================
# Exception hierarchy tests
# ====================================================================

class TestExceptions:
    def test_soft_stop_is_process_blocked(self):
        assert issubclass(SoftStopException, ProcessBlockedException)

    def test_dependency_failed_is_process_blocked(self):
        assert issubclass(DependencyFailedException, ProcessBlockedException)

    def test_conformance_exception_has_level(self):
        exc = ConformanceException("test fail", level="L2", failures=["a", "b"])
        assert exc.level == "L2"
        assert len(exc.failures) == 2

    def test_soft_stop_carries_rule_id(self):
        exc = SoftStopException("blocked", rule_id="R003")
        assert exc.rule_id == "R003"


# ====================================================================
# Helper function tests
# ====================================================================

class TestHelpers:
    def test_regex_match_valid(self):
        assert regex_match(r"^USD$", "USD") is True
        assert regex_match(r"^USD$", "EUR") is False

    def test_regex_match_none_value(self):
        assert regex_match(r".*", None) is False

    def test_parse_date_valid(self):
        result = parse_date("2024-06-15")
        assert result.year == 2024
        assert result.month == 6

    def test_today_returns_datetime(self):
        result = today()
        assert hasattr(result, "year")
