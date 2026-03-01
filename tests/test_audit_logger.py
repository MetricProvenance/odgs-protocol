import pytest
import os
import json
import shutil
from odgs.system.adapters.git_log_adapter import GitAuditLogger
from odgs.executive.interceptor import OdgsInterceptor, git_logger
import test_utils

@pytest.fixture
def audit_sandbox():
    sandbox_dir = "/tmp/odgs_audit_sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    
    test_utils.create_mock_odgs_structure(sandbox_dir)
    
    # Setup audit log dir
    audit_dir = os.path.join(sandbox_dir, ".odgs", "audit")
    os.makedirs(audit_dir, exist_ok=True)
    
    yield sandbox_dir
    
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir, ignore_errors=True)

def test_tri_partite_hash_and_agnostic_output(audit_sandbox, monkeypatch):
    audit_dir = os.path.join(audit_sandbox, ".odgs", "audit")
    git_logger.log_dir = audit_dir
    os.makedirs(audit_dir, exist_ok=True)
    
    # Initialize the interceptor which uses the GitAuditLogger internally when configured.
    # The interceptor initializes GitAuditLogger with project_root as the base.
    interceptor = OdgsInterceptor(audit_sandbox)
    
    # We load a rule that has an attestation string injected, to verify Agnostic Output
    interceptor.rules["urn:odgs:rule:custom_bypass"]["__attestation__"] = {"issuer": "did:web:test"}
    
    # Run interception
    try:
        interceptor.intercept("urn:odgs:custom:test", {"mock": "data"})
    except Exception as e:
        pytest.fail(f"Interception failed unexpectedly: {e}")
        
    # The interceptor calls `audit_logger.write_entry` which writes to `audit_YYYY-MM-DD.jsonl`
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(audit_dir, f"audit_{today}.jsonl")
    
    assert os.path.exists(log_file), f"Audit log file {log_file} was not generated."
    
    with open(log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        last_log = json.loads(lines[-1].strip())
        
    # Test 1: Tri-Partite Hash
    assert "tri_partite_binding" in last_log
    tpb = last_log["tri_partite_binding"]
    assert "payload_hash" in tpb
    assert "definition_hash" in tpb
    assert "config_hash" in tpb
    assert tpb["payload_hash"] != "HASH_ERROR_NON_SERIALIZABLE"
    
    # Test 2: Agnostic Output (no S-Cert terminology, uses cryptographic_attestation)
    assert "s_cert_status" not in last_log
    assert "cryptographic_attestation" in last_log
    assert last_log["cryptographic_attestation"] == {"issuer": "did:web:test"}
