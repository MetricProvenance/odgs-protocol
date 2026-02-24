from datetime import date, datetime
import re
import os
import json
import logging
from typing import Optional, Dict, Any

_audit_logger = logging.getLogger("sovereign_audit")

class LegalAmbiguityError(Exception):
    """Raised when a URN is resolved without a specific version or valid date."""
    pass

class ResourceNotFoundError(Exception):
    """Raised when the URN cannot be resolved to a file."""
    pass

class SovereignResolver:
    """
    The Time-Travel Resolver for ODGS.
    Ensures that every URN resolution is legally deterministic.
    """
    
    def __init__(self, data_root: str = "../1_NORMATIVE_SPECIFICATION/schemas"):
        self.data_root = data_root

    def resolve(self, urn: str, as_of_date: Optional[date] = None, force_latest: bool = False) -> Dict[str, Any]:
        """
        Resolves a URN to a Sovereign Definition or Schema Object.
        
        Args:
            urn: The URN to resolve (e.g., 'urn:odgs:def:nl_gov:awb:v2024').
            as_of_date: The legal date for which the definition is required.
            force_latest: If True, bypasses the date check and returns the latest version. DANGEROUS.
            
        Returns:
            Dict: The resolved JSON object.
            
        Raises:
            LegalAmbiguityError: If URN is versionless and no date/force flag is provided.
            ResourceNotFoundError: If the resource does not exist.
        """
        parsed = self._parse_urn(urn)
        
        # Case 1: Pinned Version (Safe)
        if parsed['version']:
            return self._fetch_specific_version(parsed)
            
        # Case 2: Naked URN (Unsafe)
        if as_of_date is None and not force_latest:
            raise LegalAmbiguityError(
                f"Resolution of versionless URN '{urn}' requires 'as_of_date' or 'force_latest=True'."
            )

        if force_latest:
            _audit_logger.warning(
                f"DANGEROUS: force_latest=True used for URN '{urn}'. "
                "Legal determinism bypassed — this event is recorded."
            )

        # Case 3: Time-Travel Resolution
        return self._resolve_by_date(parsed, as_of_date)

    def _parse_urn(self, urn: str) -> Dict[str, str]:
        """Parses URN into components.
        
        Supports formats like:
          urn:odgs:metric:101
          urn:odgs:def:nl_gov:awb:art_1_3:v2024
          urn:odgs:rule:2001
        """
        # First, try the extended sovereign format: urn:odgs:<domain>:<...segments...>:<version>
        # Version is always v<digits> at the end.
        match = re.match(
            r"urn:odgs:(?P<domain>[a-z_]+):(?P<id>.+?)(?::(?P<version>v[0-9.]+))?$", 
            urn
        )
        if not match:
            raise ValueError(f"Invalid URN format: {urn}")
        return match.groupdict()

    def _fetch_specific_version(self, parsed: Dict[str, str]) -> Dict[str, Any]:
        """Fetches the exact file for a versioned URN."""
        # Implementation assumes a standard file path structure
        # lib/data/sovereign/<domain>/<id>_<version>.json
        # This is a placeholder for the actual storage logic.
        file_path = os.path.join(
            self.data_root, 
            "sovereign", # Assuming storage in sovereign dir
            parsed['domain'], 
            f"{parsed['id']}_{parsed['version']}.json"
        ).replace(":", "_")
        
        if not os.path.exists(file_path):
            # Check if it's a schema/meta definition (e.g. Metric 101)
            # which are currently single files.
            # Fallback to standard schemas for non-sovereign types.
            return self._fetch_standard_schema(parsed)

        with open(file_path, 'r') as f:
            return json.load(f)

    def _resolve_by_date(self, parsed: Dict[str, str], target_date: Optional[date]) -> Dict[str, Any]:
        """
        Finds the version effective on the given date.
        Scans the sovereign/<domain>/ directory for versioned files,
        sorts by version date, and selects the latest version ≤ target_date.
        """
        sovereign_dir = os.path.join(
            self.data_root, "sovereign", parsed['domain']
        )
        
        if not os.path.isdir(sovereign_dir):
            # No versioned sovereign directory exists — fall back to standard schema
            _audit_logger.info(
                f"No sovereign versioned directory for '{parsed['domain']}'. "
                f"Falling back to standard schema."
            )
            return self._fetch_standard_schema(parsed)
        
        # Pattern: <id>_v<YYYY>.<MM>.json or <id>_v<YYYY>.json
        prefix = parsed['id'].replace(":", "_")
        candidates = []
        
        for fname in os.listdir(sovereign_dir):
            if not fname.startswith(prefix) or not fname.endswith(".json"):
                continue
            # Extract version from filename
            version_match = re.search(r"_v(\d{4})(?:\.(\d{1,2}))?(?:\.(\d{1,2}))?\.json$", fname)
            if version_match:
                year = int(version_match.group(1))
                month = int(version_match.group(2) or 1)
                day = int(version_match.group(3) or 1)
                version_date = date(year, month, day)
                candidates.append((version_date, fname))
        
        if not candidates:
            _audit_logger.info(
                f"No versioned files found for '{parsed['id']}' in sovereign dir. "
                f"Falling back to standard schema."
            )
            return self._fetch_standard_schema(parsed)
        
        # Sort by date descending, filter to those ≤ target_date
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        effective_date = target_date if target_date else date.today()
        valid = [(d, f) for d, f in candidates if d <= effective_date]
        
        if not valid:
            raise ResourceNotFoundError(
                f"No version of '{parsed['id']}' is effective on or before {effective_date}."
            )
        
        chosen_date, chosen_file = valid[0]
        _audit_logger.info(
            f"Time-travel resolved '{parsed['id']}' to version dated {chosen_date} "
            f"(requested: {effective_date})."
        )
        
        filepath = os.path.join(sovereign_dir, chosen_file)
        with open(filepath, 'r') as f:
            return json.load(f)

    def resolve_context(self, context_id: str, as_of_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Resolves a context binding with temporal awareness.
        Returns the context that is effective for the given date.
        """
        bindings_path = os.path.join(self.data_root, "executive", "context_bindings.json")
        if not os.path.exists(bindings_path):
            return None
        
        with open(bindings_path, 'r') as f:
            bindings = json.load(f)
        
        check_date = as_of_date if as_of_date else date.today()
        
        for ctx in bindings.get("contexts", []):
            if ctx["context_id"] != context_id:
                continue
            
            # Check temporal validity
            eff_from = ctx.get("effective_from")
            eff_until = ctx.get("effective_until")
            
            if eff_from:
                from_date = date.fromisoformat(eff_from)
                if check_date < from_date:
                    continue
            
            if eff_until:
                until_date = date.fromisoformat(eff_until)
                if check_date > until_date:
                    continue
            
            return ctx
        
        return None

    def _fetch_standard_schema(self, parsed: Dict[str, str]) -> Dict[str, Any]:
        """Fallback to fetching from the core schemas (Metrics, Rules, Dimensions)."""
        domain_files = {
            "metric": "legislative/standard_metrics.json",
            "rule": "judiciary/standard_data_rules.json",
            "dimension": "legislative/standard_dq_dimensions.json"
        }
        
        if parsed['domain'] not in domain_files:
             raise ResourceNotFoundError(f"Unknown domain: {parsed['domain']}")
             
        path = os.path.join(self.data_root, domain_files[parsed['domain']])
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            target_urn = f"urn:odgs:{parsed['domain']}:{parsed['id']}"
            
            for item in data:
                # Check explicit URN field first
                if item.get('urn') == target_urn:
                    return item
                # Fallback for metrics (keyed by metric_id)
                if parsed['domain'] == 'metric' and str(item.get('metric_id')) == parsed['id']:
                    return item
                # Fallback for rules (keyed by rule_id)
                if parsed['domain'] == 'rule' and str(item.get('rule_id')) == parsed['id']:
                    return item
                # Fallback for dimensions (keyed by id)
                if parsed['domain'] == 'dimension' and str(item.get('id')) == parsed['id']:
                    return item

        except FileNotFoundError:
            pass
            
        raise ResourceNotFoundError(f"Could not find resource for URN: urn:odgs:{parsed['domain']}:{parsed['id']}")

