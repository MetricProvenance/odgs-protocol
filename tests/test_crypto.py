import pytest
import json
import os
import shutil
from unittest.mock import patch
import jwt
from jwcrypto import jwk

from odgs.core.crypto import CryptoResolver, SecurityException

@pytest.fixture(scope="module")
def mock_keys():
    # Generate RSA keypair for testing
    key = jwk.JWK.generate(kty='RSA', size=2048, kid='mock-kid-1')
    private_pem = key.export_to_pem(private_key=True, password=None)
    jwks_dict = {"keys": [json.loads(key.export_public())]}
    
    return {
        "private_pem": private_pem,
        "jwks": jwks_dict
    }

@pytest.fixture
def crypto_sandbox(mock_keys):
    # Setup isolated test directory
    sandbox_dir = "/tmp/odgs_crypto_sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    
    # Create mock authorities.json
    auth_path = os.path.join(sandbox_dir, "authorities.json")
    mock_auth = {
        "did:web:mock.test": "https://mock.test/.well-known/jwks.json"
    }
    with open(auth_path, "w") as f:
        json.dump(mock_auth, f)
        
    resolver = CryptoResolver(auth_path)
    
    yield resolver, sandbox_dir
    
    # Teardown
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)

class TestCryptoresolver:
    
    @patch('jwt.PyJWKClient.fetch_data')
    def test_valid_signature_verification(self, mock_fetch, crypto_sandbox, mock_keys):
        resolver, sandbox_dir = crypto_sandbox
        
        # Mock fetch_data to return the raw dictionary
        mock_fetch.return_value = mock_keys["jwks"]
        
        # Create a valid pack payload
        pack_payload = {
            "rules": [
                {"rule_id": "test_1", "urn": "urn:odgs:sov:test:1"}
            ]
        }
        
        # Sign it with our private key
        # Following Python SDK format assumption: payload hash is signed
        import hashlib
        payload_str = json.dumps(pack_payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        token_payload = {
            "iss": "did:web:mock.test",
            "file_hash": payload_hash
        }
        
        signature = jwt.encode(
            token_payload, 
            mock_keys["private_pem"], 
            algorithm="RS256", 
            headers={"kid": "mock-kid-1"}
        )
        
        pack_payload["signature"] = signature
        
        # Execute verification
        verified_headers = resolver.verify_pack_signature("dummy_path.json", signature, pack_payload)
        
        # Assertions
        assert verified_headers is not None
        assert verified_headers["kid"] == "mock-kid-1"
        assert verified_headers["iss"] == "did:web:mock.test"

    @patch('jwt.PyJWKClient.fetch_data')
    def test_tampered_payload_rejected(self, mock_fetch, crypto_sandbox, mock_keys):
        resolver, sandbox_dir = crypto_sandbox
        
        # Mock fetch_data
        mock_fetch.return_value = mock_keys["jwks"]
        
        # Create a valid pack payload and sign it
        pack_payload = {
            "rules": [
                {"rule_id": "test_1", "urn": "urn:odgs:sov:test:1"}
            ]
        }
        
        import hashlib
        payload_str = json.dumps(pack_payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        token_payload = {
            "iss": "did:web:mock.test",
            "file_hash": payload_hash
        }
        
        signature = jwt.encode(
            token_payload, 
            mock_keys["private_pem"], 
            algorithm="RS256", 
            headers={"kid": "mock-kid-1"}
        )
        
        # Maliciously TAMPER with the JSON payload after it was signed
        tampered_payload = {
            "rules": [
                {"rule_id": "test_1", "urn": "urn:odgs:sov:test:1_TAMPERED"}
            ],
            "signature": signature
        }
        
        # Verify it raises SecurityException
        with pytest.raises(SecurityException) as exc_info:
            resolver.verify_pack_signature("dummy_path.json", signature, tampered_payload)
            
        assert "Content hash mismatch" in str(exc_info.value)

    @patch('jwt.PyJWKClient.fetch_data')
    def test_jwks_spoofing_rejected(self, mock_fetch, crypto_sandbox, mock_keys):
        resolver, sandbox_dir = crypto_sandbox
        
        # Mock JWKS endpoint (Returning the REAL keys)
        mock_fetch.return_value = mock_keys["jwks"]
        
        # Attacker tries to use an invalid/unknown KID
        pack_payload = {
            "rules": [{"rule_id": "test_1", "urn": "urn:odgs:sov:test:1"}]
        }
        
        import hashlib
        payload_str = json.dumps(pack_payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        token_payload = {
            "iss": "did:web:mock.test",
            "file_hash": payload_hash
        }
        
        # Sign with some unrelated private key
        malicious_key = jwk.JWK.generate(kty='RSA', size=2048, kid='attacker-kid-99')
        malicious_pem = malicious_key.export_to_pem(private_key=True, password=None)
        
        signature = jwt.encode(
            token_payload, 
            malicious_pem, 
            algorithm="RS256", 
            headers={"kid": "attacker-kid-99"}
        )
        
        pack_payload["signature"] = signature
        
        with pytest.raises(SecurityException) as exc_info:
            resolver.verify_pack_signature("dummy_path.json", signature, pack_payload)
            
        assert "Unable to find a signing key that matches" in str(exc_info.value)
