from ..core import BaseHarvester, HarvesterException
import urllib.request
import ssl
import json
from typing import Dict, Any, List

class FIBOHarvester(BaseHarvester):
    """
    Harvester for the Financial Industry Business Ontology (FIBO).
    Source: spec.edmcouncil.org

    FIBO is organized into modules (e.g., FND/Accounting/CurrencyAmount).
    This harvester dynamically routes concept requests to the appropriate
    FIBO module using a routing table, rather than being hardcoded to a
    single JSONLD endpoint.

    Usage:
        harvester = FIBOHarvester()
        result = harvester.harvest("InterestRate")      # Routes to CurrencyAmount
        result = harvester.harvest("AccountingEquity")   # Routes to AccountingEquity
    """
    
    BASE_URL_TEMPLATE = "https://spec.edmcouncil.org/fibo/ontology/master/latest/{module}.jsonld"
    
    # ------------------------------------------------------------------ #
    # MODULE ROUTING TABLE                                                 #
    # Maps concept names to their FIBO module path.                        #
    # To add a new concept: add an entry here — zero code changes needed.  #
    # ------------------------------------------------------------------ #
    FIBO_MODULES: Dict[str, Dict[str, Any]] = {
        # --- FND / Accounting ---
        "InterestRate": {
            "module": "FND/Accounting/CurrencyAmount",
            "description": "Interest rate definitions and currency amount concepts",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FND/Accounting/CurrencyAmount/"
        },
        "AccountingEquity": {
            "module": "FND/Accounting/AccountingEquity",
            "description": "Equity, net income, owner's equity, and retained earnings",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FND/Accounting/AccountingEquity/"
        },
        "CurrencyAmount": {
            "module": "FND/Accounting/CurrencyAmount",
            "description": "Monetary amounts and currency identifiers",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FND/Accounting/CurrencyAmount/"
        },
        # --- FND / Organizations ---
        "LegalEntity": {
            "module": "FND/Organizations/FormalOrganizations",
            "description": "Legal entities, organizations, and corporate structures",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FND/Organizations/FormalOrganizations/"
        },
        # --- FBC / Financial Business and Commerce ---
        "FinancialInstrument": {
            "module": "FBC/FinancialInstruments/FinancialInstruments",
            "description": "Financial instruments including securities and derivatives",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FBC/FinancialInstruments/FinancialInstruments/"
        },
        "RegulatoryAgency": {
            "module": "FBC/FunctionalEntities/RegulatoryAgencies",
            "description": "Regulatory bodies and their jurisdictions",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/FBC/FunctionalEntities/RegulatoryAgencies/"
        },
        # --- LOAN / Loans ---
        "Loan": {
            "module": "LOAN/LoansGeneral/Loans",
            "description": "Loan contracts, terms, and conditions",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/LOAN/LoansGeneral/Loans/"
        },
        # --- SEC / Securities ---
        "DebtInstrument": {
            "module": "SEC/Debt/DebtInstruments",
            "description": "Debt instruments including bonds and notes",
            "source_url": "https://spec.edmcouncil.org/fibo/ontology/SEC/Debt/DebtInstruments/"
        },
    }

    # Fallback module when the concept is not in the routing table
    DEFAULT_MODULE = "FND/Accounting/CurrencyAmount"

    def _resolve_module_url(self, reference_id: str) -> str:
        """Resolve the JSONLD URL for a given concept using the routing table."""
        if reference_id in self.FIBO_MODULES:
            module_path = self.FIBO_MODULES[reference_id]["module"]
        else:
            # Try to find a partial match (case insensitive)
            for concept_name, info in self.FIBO_MODULES.items():
                if concept_name.lower() == reference_id.lower():
                    module_path = info["module"]
                    break
            else:
                print(f"  ⚠ Concept '{reference_id}' not in routing table. Trying default module: {self.DEFAULT_MODULE}")
                module_path = self.DEFAULT_MODULE
        
        return self.BASE_URL_TEMPLATE.format(module=module_path)

    @classmethod
    def list_available_concepts(cls) -> List[Dict[str, str]]:
        """List all concepts available in the routing table."""
        return [
            {
                "concept": name,
                "module": info["module"],
                "description": info["description"],
                "source_url": info["source_url"]
            }
            for name, info in cls.FIBO_MODULES.items()
        ]

    def harvest(self, reference_id: str) -> Dict[str, Any]:
        """
        Harvests a specific Concept from FIBO.
        
        The concept is routed to the appropriate FIBO module via the
        FIBO_MODULES routing table. If the concept is not in the table,
        it falls back to the CurrencyAmount module.

        Args:
            reference_id: The Concept Name (e.g. "InterestRate", "AccountingEquity")
            
        Returns:
            Dict: SovereignDefinition
        """
        url = self._resolve_module_url(reference_id)
        print(f"  🌐 Fetching FIBO JSON-LD from {url}...")
        
        try:
            ssl_ctx = ssl.create_default_context()
            with urllib.request.urlopen(url, context=ssl_ctx, timeout=30) as response:
                data = json.load(response)
        except Exception as e:
            raise HarvesterException(f"Failed to fetch FIBO JSON-LD from {url}: {e}")

        # The JSON-LD is usually a list of objects or a @graph
        graph = data.get("@graph", data) if isinstance(data, dict) else data
        
        target_node = None
        target_id_suffix = f"/{reference_id}"
        
        # Search for the concept in the graph
        for node in graph:
            node_id = node.get("@id", "")
            if node_id.endswith(target_id_suffix) or node_id.endswith(f":{reference_id}"):
                target_node = node
                break
        
        if target_node is None:
            raise HarvesterException(
                f"Concept '{reference_id}' not found in FIBO module at {url}.\n"
                f"  Available concepts: {', '.join(self.FIBO_MODULES.keys())}\n"
                f"  Tip: Use FIBOHarvester.list_available_concepts() to see all routable concepts."
            )

        # Extract definition text (FIBO uses skos:definition, rdfs:comment, or rdfs:label)
        definition_text = (
            target_node.get("skos:definition") 
            or target_node.get("rdfs:comment") 
            or target_node.get("rdfs:label")
        )
        
        if not definition_text:
            print(f"  ⚠ No definition text found for {reference_id}. Using ID as verbatim text.")
            definition_text = f"Concept: {reference_id} ({target_node.get('@id')})"
        
        if isinstance(definition_text, list):
            definition_text = definition_text[0]

        # Extract relations (subClassOf)
        relations = []
        sub_class = target_node.get("rdfs:subClassOf")
        if sub_class:
            if isinstance(sub_class, dict):
                sub_class = [sub_class]
            elif isinstance(sub_class, str):
                sub_class = [{"@id": sub_class}]
            
            if isinstance(sub_class, list):
                for sc in sub_class:
                    if isinstance(sc, dict) and "@id" in sc:
                        target_uri = sc["@id"]
                        term = target_uri.split("/")[-1].split(":")[-1]
                        relations.append({
                            "type": "subClassOf",
                            "target_urn": f"urn:odgs:def:fibo:{term.lower()}"
                        })

        # Construct SovereignDefinition
        urn = f"urn:odgs:def:fibo:{reference_id.lower()}:v2024"
        
        # Resolve module info for metadata
        module_info = self.FIBO_MODULES.get(reference_id, {})
        
        definition = {
            "urn": urn,
            "metadata": {
                "authority_id": "FIBO",
                "authority_name": "Financial Industry Business Ontology",
                "document_ref": "FIBO Master",
                "source_uri": target_node.get("@id"),
                "module": module_info.get("module", self.DEFAULT_MODULE),
                "hierarchy": {
                    "level": "concept",
                    "local_id": reference_id
                }
            },
            "relations": relations,
            "content": {
                "verbatim_text": definition_text,
                "language": "en-US",
                "format": "JSON_LD",
                "structured_data": target_node 
            },
            "interpretation": {
                "summary": f"FIBO definition of {reference_id}",
                "applicability": "Financial Sector"
            }
        }
        
        return definition
