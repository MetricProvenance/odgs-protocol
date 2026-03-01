import json
import logging
import hashlib
from typing import Dict, Any

try:
    import jwt
    from jwt import PyJWKClient
except ImportError:
    jwt = None
    PyJWKClient = None

logger = logging.getLogger("sovereign_audit")

class SecurityException(Exception):
    """Raised when a Cryptographic Handshake failure occurs."""
    pass

class CryptoResolver:
    def __init__(self, authorities_path: str):
        self.authorities_path = authorities_path
        self.authorities = {}
        self.jwks_clients = {}
        self._load_authorities()

    def _load_authorities(self):
        try:
            with open(self.authorities_path, 'r') as f:
                self.authorities = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load authorities from {self.authorities_path}: {e}")

    def _fetch_public_key(self, issuer: str, kid: str):
        if not PyJWKClient:
            raise SecurityException("PyJWT library is missing. Cannot perform cryptographic verification.")

        jwks_uri = self.authorities.get(issuer)
        if not jwks_uri:
            raise SecurityException(f"Unknown issuer: '{issuer}'. No JWKS endpoint registered in authorities.json.")

        if issuer not in self.jwks_clients:
            self.jwks_clients[issuer] = PyJWKClient(jwks_uri, cache_keys=True)

        try:
            jwks_client = self.jwks_clients[issuer]
            signing_key = jwks_client.get_signing_key(kid)
            return signing_key.key
        except Exception as e:
            raise SecurityException(f"Failed to fetch public key for issuer '{issuer}' and kid '{kid}': {e}")

    def verify_pack_signature(self, file_path: str, signature_payload: str, pack_data: Dict[str, Any] = None):
        """
        1. Hashes the physical JSON file loaded from disk (excluding the signature itself).
        2. Decodes the provided JWS signature.
        3. Uses _fetch_public_key to get the public key.
        4. Mathematically verifies that the signature matches the file hash.
        """
        if not jwt:
            raise SecurityException("PyJWT library is missing.")

        try:
            # Hash canonical JSON
            if pack_data is None:
                with open(file_path, 'r') as f:
                    pack_data = json.load(f)

            import copy
            data_to_hash = copy.deepcopy(pack_data)
            data_to_hash.pop("signature", None)
            
            canonical_content = json.dumps(data_to_hash, sort_keys=True, separators=(',', ':'))
            file_hash = hashlib.sha256(canonical_content.encode('utf-8')).hexdigest()

            # Decode headers to extract kid
            unverified_headers = jwt.get_unverified_header(signature_payload)
            kid = unverified_headers.get('kid')

            # Decode unverified payload to extract issuer (iss)
            unverified_payload = jwt.decode(signature_payload, options={"verify_signature": False})
            issuer = unverified_payload.get("iss")

            if not kid:
                raise SecurityException("JWS is missing 'kid' in header.")
            if not issuer:
                raise SecurityException("JWS is missing 'iss' (issuer) in payload.")

            # Fetch Key
            public_key = self._fetch_public_key(issuer, kid)

            # Verify
            decoded_payload = jwt.decode(
                signature_payload,
                public_key,
                algorithms=["RS256", "ES256", "HS256"],
                issuer=issuer,
                options={"verify_signature": True, "verify_iss": True}
            )

            payload_hash = decoded_payload.get("file_hash")
            if not payload_hash:
                raise SecurityException("The signature payload does not contain a 'file_hash' claim.")

            if payload_hash != file_hash:
                raise SecurityException(
                    f"Signature verification failed: Content hash mismatch. "
                    f"Expected {payload_hash}, but file hashed to {file_hash}."
                )

            return {
                "iss": issuer,
                "kid": kid
            }

        except jwt.PyJWTError as e:
            raise SecurityException(f"JWT Verification Error: {str(e)}")
        except SecurityException:
            raise
        except Exception as e:
            raise SecurityException(f"Cryptographic validation failed: {str(e)}")
