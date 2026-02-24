"""
ODGS Integration Test Pipeline
Tests the full end-to-end sovereign interception flow:
1. Schema loading
2. Sovereign Handshake (integrity hash verification)
3. Rule evaluation (PASS + BLOCK scenarios)
4. Audit log generation with Tri-Partite Binding
"""
import os
import sys
import json
import unittest

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException
from odgs.system.scripts.hashing import generate_project_hash


class TestIntegrationPipeline(unittest.TestCase):
    """End-to-end integration tests for the ODGS Sovereign Sidecar."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize interceptor once for all tests."""
        cls.odgs_root = os.path.join(project_root, "src", "odgs")
        cls.interceptor = OdgsInterceptor(cls.odgs_root)
        cls.real_hash = generate_project_hash(cls.odgs_root)["master_hash"]

    # ── 1. Schema Loading ──────────────────────────────────────

    def test_01_schemas_loaded(self) -> None:
        """All core schemas should load without error."""
        self.assertIsNotNone(self.interceptor.graph, "Ontology graph should be loaded")
        self.assertGreater(len(self.interceptor.rules), 0, "Rules should be loaded")
        self.assertIsNotNone(self.interceptor.metrics, "Metrics should be loaded")

    def test_02_rules_indexed_by_urn(self) -> None:
        """Rules should be indexed by URN key (urn:odgs:rule:XXXX)."""
        for key in self.interceptor.rules:
            self.assertTrue(
                key.startswith("urn:odgs:rule:"),
                f"Rule key '{key}' should be URN-formatted"
            )

    # ── 2. Sovereign Handshake ─────────────────────────────────

    def test_03_handshake_passes_with_valid_hash(self) -> None:
        """Intercept should succeed when provided the correct integrity hash."""
        result = self.interceptor.intercept(
            "urn:odgs:process:integration_test",
            {"value": 100},
            required_integrity_hash=self.real_hash
        )
        self.assertTrue(result)

    def test_04_handshake_fails_with_tampered_hash(self) -> None:
        """SecurityException should be raised when the hash is tampered."""
        with self.assertRaises(SecurityException) as ctx:
            self.interceptor.intercept(
                "urn:odgs:process:integration_test",
                {"value": 100},
                required_integrity_hash="TAMPERED_HASH_0000000000000000"
            )
        # The interceptor says "CRITICAL SECURITY FAILURE" in its error message
        self.assertIn("CRITICAL SECURITY FAILURE", str(ctx.exception))

    # ── 3. Rule Evaluation (via intercept) ─────────────────────

    def test_05_unbound_process_passes(self) -> None:
        """A process with no BLOCKS_PROCESS edges should always pass."""
        result = self.interceptor.intercept(
            "urn:odgs:process:unbound_test",
            {"value": 42},
            required_integrity_hash=self.real_hash
        )
        self.assertTrue(result)

    def test_06_blocking_rule_with_bad_data(self) -> None:
        """O2C_S03 is blocked by rule 2021; invalid container_id should fail."""
        with self.assertRaises(ProcessBlockedException) as ctx:
            self.interceptor.intercept(
                "urn:odgs:process:O2C_S03",
                {"container_id": "BAD", "value": "INVALID_CONTAINER"},
                required_integrity_hash=self.real_hash
            )
        # The interceptor raises "HARD STOP" for individual rule failures
        self.assertIn("HARD STOP", str(ctx.exception))

    def test_07_unlinked_process_passes(self) -> None:
        """A process not linked to any BLOCKS_PROCESS edge should pass."""
        result = self.interceptor.intercept(
            "urn:odgs:process:no_blocking_rules",
            {"container_id": "MSKU1234567", "value": 100},
            required_integrity_hash=self.real_hash
        )
        self.assertTrue(result)

    # ── 4. Exception Types ─────────────────────────────────────

    def test_08_security_exception_is_exception(self) -> None:
        """SecurityException should be a valid Python Exception."""
        exc = SecurityException("test")
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), "test")

    def test_09_process_blocked_is_exception(self) -> None:
        """ProcessBlockedException should be a valid Python Exception."""
        exc = ProcessBlockedException("test")
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), "test")

    # ── 5. Full Pipeline (End-to-End) ──────────────────────────

    def test_10_full_pipeline_approved(self) -> None:
        """Full pipeline: valid hash + no blocking rules → APPROVED."""
        result = self.interceptor.intercept(
            "urn:odgs:process:pipeline_test_pass",
            {"container_id": "MSKU1234567", "value": 100},
            required_integrity_hash=self.real_hash
        )
        self.assertTrue(result)

    def test_11_full_pipeline_blocked(self) -> None:
        """Full pipeline: blocking rule with invalid data → BLOCKED."""
        with self.assertRaises(ProcessBlockedException):
            self.interceptor.intercept(
                "urn:odgs:process:O2C_S03",
                {"container_id": "BAD", "value": "INVALID_CONTAINER"},
                required_integrity_hash=self.real_hash
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
