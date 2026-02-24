import json
import hashlib
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class HarvesterException(Exception):
    """Base exception for harvesting errors."""
    pass

class BaseHarvester(ABC):
    """
    Abstract Base Class for Sovereign Harvesters.
    """
    
    def __init__(self, output_dir: str = "../1_NORMATIVE_SPECIFICATION/schemas/sovereign"):
        self.output_dir = output_dir
        # Ensure output directory exists (handled by save but good practice)
        os.makedirs(self.output_dir, exist_ok=True)

    @abstractmethod
    def harvest(self, reference_id: str) -> Dict[str, Any]:
        """
        Fetch data from the Sovereign Source and return a valid SovereignDefinition.
        
        Args:
            reference_id: The ID to fetch (e.g. "1:3" or "InterestRate")
            
        Returns:
            Dict: The SovereignDefinition JSON object.
        """
        pass

    def save(self, definition: Dict[str, Any]) -> str:
        """
        Validates, Hashes, and Saves the definition to disk.
        
        Returns:
            str: The path to the saved file.
        """
        # 1. Validate Structure (Basic Check)
        if "urn" not in definition or "content" not in definition:
            raise HarvesterException("Invalid Definition: Missing 'urn' or 'content'.")

        # 2. Calculate Content Hash (SHA-256)
        # We hash the verbatim_text to ensure immutability of the "Law"
        text = definition["content"].get("verbatim_text", "")
        if not text:
            raise HarvesterException("Invalid Definition: Missing 'verbatim_text'.")
            
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        definition["metadata"]["content_hash"] = content_hash
        definition["metadata"]["harvested_at"] = datetime.utcnow().isoformat() + "Z"

        # 3. Construct Filename
        # urn:odgs:def:nl_gov:awb:art_1_3 -> nl_gov/awb/art_1_3.json ? 
        # Or just flat for now? The generic structure suggests:
        # ../1_NORMATIVE_SPECIFICATION/schemas/sovereign/<authority_id>/<filename>.json
        
        auth_id = definition["metadata"]["authority_id"].lower()
        urn_parts = definition["urn"].split(":")
        # urn:odgs:def:<auth>:<ref>:<ver> -> ref_ver.json
        ref_id = urn_parts[4]
        version = urn_parts[5] if len(urn_parts) > 5 else "latest"
        
        filename = f"{ref_id}_{version}.json".replace(":", "_")
        
        save_dir = os.path.join(self.output_dir, auth_id)
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, filename)
        
        with open(save_path, 'w') as f:
            json.dump(definition, f, indent=2)
            
        return save_path
