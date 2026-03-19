"""
Tests for odgs v5.1.0 new features:
  - Complete S-Cert audit fields (rule_id, semantic_hash, system_id, payload_hash)
  - LOG_ONLY verdict mode (non-blocking)
  - Rule lifecycle — temporal bounds (effective_from / effective_to)
"""
import pytest
import os
import json
import shutil
import datetime
from odgs.executive.interceptor import OdgsInterceptor, git_logger
import test_utils


@pytest.fixture
def sandbox(tmp_path):
    """Standard sandbox with the minimal ODGS structure."""
    base = str(tmp_path)
    test_utils.create_mock_odgs_structure(base)
    audit_dir = os.path.join(base, ".odgs", "audit")
    os.makedirs(audit_dir, exist_ok=True)
    git_logger.log_dir = audit_dir
    yield base


def _last_audit_entry(sandbox):
    """Read the last line of today's audit log from the sandbox."""
    audit_dir = os.path.join(sandbox, ".odgs", "audit")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(audit_dir, f"audit_{today}.jsonl")
    assert os.path.exists(log_file), f"Audit log not found: {log_file}"
    with open(log_file) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert lines, "Audit log is empty"
    return json.loads(lines[-1])


# ---------------------------------------------------------------------------
# S-Cert Annex A mandatory fields
# ---------------------------------------------------------------------------

def test_scert_has_annex_a_mandatory_fields(sandbox):
    """v5.1.0: S-Cert must contain all required audit fields."""
    interceptor = OdgsInterceptor(sandbox)
    interceptor.intercept("urn:odgs:custom:test", {"value": 42})

    entry = _last_audit_entry(sandbox)

    # ODGS S-Cert — all required fields
    assert "event_id" in entry
    assert "timestamp" in entry
    assert "process_urn" in entry
    assert "rule_id" in entry
    assert "semantic_hash" in entry
    assert "verdict" in entry
    assert "system_id" in entry
    assert "payload_hash" in entry


def test_payload_hash_is_sha256_of_input(sandbox):
    """payload_hash must be the SHA-256 of the canonical input JSON (zero-knowledge auditing)."""
    import hashlib
    data = {"value": 42}
    interceptor = OdgsInterceptor(sandbox)
    interceptor.intercept("urn:odgs:custom:test", data)

    entry = _last_audit_entry(sandbox)
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    expected_hash = hashlib.sha256(canonical.encode()).hexdigest()
    assert entry["payload_hash"] == expected_hash


def test_payload_hash_does_not_contain_raw_payload(sandbox):
    """S-Cert must NOT contain raw payload — only its hash (zero-knowledge auditing)."""
    data = {"sensitive_field": "PII_DATA_SECRET_123"}
    interceptor = OdgsInterceptor(sandbox)
    interceptor.intercept("urn:odgs:custom:test", data)

    entry = _last_audit_entry(sandbox)
    entry_str = json.dumps(entry)
    assert "PII_DATA_SECRET_123" not in entry_str, "Raw PII leaked into audit log!"


def test_system_id_present(sandbox, monkeypatch):
    """system_id is set from ODGS_SYSTEM_ID env var or hostname fallback."""
    monkeypatch.setenv("ODGS_SYSTEM_ID", "test-deployment-node-1")
    interceptor = OdgsInterceptor(sandbox)
    interceptor.intercept("urn:odgs:custom:test", {"value": 1})
    entry = _last_audit_entry(sandbox)
    assert entry["system_id"] == "test-deployment-node-1"


# ---------------------------------------------------------------------------
# LOG_ONLY verdict — non-blocking
# ---------------------------------------------------------------------------

def test_log_only_rule_does_not_raise(sandbox):
    """A rule with severity=LOG_ONLY that fails must NOT block processing."""
    interceptor = OdgsInterceptor(sandbox)
    # Inject a rule that always fails but is LOG_ONLY
    interceptor.rules["urn:odgs:rule:log_only_test"] = {
        "rule_id": "log_only_test",
        "urn": "urn:odgs:rule:log_only_test",
        "name": "Always Fails LOG_ONLY",
        "logic_expression": "False",
        "severity": "LOG_ONLY",
    }
    interceptor.bindings["contexts"].append({
        "context_id": "urn:odgs:custom:log_only",
        "rules": ["urn:odgs:rule:log_only_test"]
    })

    # Must NOT raise — LOG_ONLY means silent observation only
    result = interceptor.intercept("urn:odgs:custom:log_only", {"value": 1})
    assert result is True


def test_log_only_event_recorded_in_audit(sandbox):
    """LOG_ONLY failure must appear in log_only_events list in the audit entry."""
    interceptor = OdgsInterceptor(sandbox)
    interceptor.rules["urn:odgs:rule:log_only_rec"] = {
        "rule_id": "log_only_rec",
        "urn": "urn:odgs:rule:log_only_rec",
        "name": "Record Me",
        "logic_expression": "False",
        "severity": "LOG_ONLY",
    }
    interceptor.bindings["contexts"].append({
        "context_id": "urn:odgs:custom:log_rec",
        "rules": ["urn:odgs:rule:log_only_rec"]
    })

    interceptor.intercept("urn:odgs:custom:log_rec", {"value": 1})
    entry = _last_audit_entry(sandbox)
    assert "log_only_events" in entry
    assert any("log_only_rec" in e for e in entry["log_only_events"])


# ---------------------------------------------------------------------------
# Temporal bounds — effective_from / effective_to
# ---------------------------------------------------------------------------

def test_rule_with_future_effective_from_is_skipped(sandbox):
    """A rule with effective_from in the future must be silently skipped."""
    interceptor = OdgsInterceptor(sandbox)
    future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    interceptor.rules["urn:odgs:rule:future_rule"] = {
        "rule_id": "future_rule",
        "urn": "urn:odgs:rule:future_rule",
        "name": "Not Yet Active",
        "logic_expression": "False",   # Would HARD_STOP if evaluated
        "severity": "HARD_STOP",
        "effective_from": future_date,
    }
    interceptor.bindings["contexts"].append({
        "context_id": "urn:odgs:custom:future",
        "rules": ["urn:odgs:rule:future_rule"]
    })

    # Must NOT raise — rule is not yet effective
    result = interceptor.intercept("urn:odgs:custom:future", {"value": 1})
    assert result is True


def test_rule_with_past_effective_to_is_skipped(sandbox):
    """A rule with effective_to in the past must be silently skipped (sunsetted)."""
    interceptor = OdgsInterceptor(sandbox)
    past_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    interceptor.rules["urn:odgs:rule:expired_rule"] = {
        "rule_id": "expired_rule",
        "urn": "urn:odgs:rule:expired_rule",
        "name": "Expired Rule",
        "logic_expression": "False",   # Would HARD_STOP if evaluated
        "severity": "HARD_STOP",
        "effective_to": past_date,
    }
    interceptor.bindings["contexts"].append({
        "context_id": "urn:odgs:custom:expired",
        "rules": ["urn:odgs:rule:expired_rule"]
    })

    result = interceptor.intercept("urn:odgs:custom:expired", {"value": 1})
    assert result is True


def test_rule_within_effective_window_is_enforced(sandbox):
    """A rule whose effective window covers today must be evaluated and can block."""
    from odgs.executive.exceptions import ProcessBlockedException
    interceptor = OdgsInterceptor(sandbox)
    past = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    future = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    interceptor.rules["urn:odgs:rule:active_rule"] = {
        "rule_id": "active_rule",
        "urn": "urn:odgs:rule:active_rule",
        "name": "Active Rule",
        "logic_expression": "False",   # Always fails
        "severity": "HARD_STOP",
        "effective_from": past,
        "effective_to": future,
    }
    interceptor.bindings["contexts"].append({
        "context_id": "urn:odgs:custom:active",
        "rules": ["urn:odgs:rule:active_rule"]
    })

    with pytest.raises(ProcessBlockedException):
        interceptor.intercept("urn:odgs:custom:active", {"value": 1})
