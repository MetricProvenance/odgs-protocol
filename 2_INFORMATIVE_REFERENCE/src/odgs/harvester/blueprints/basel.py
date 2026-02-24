"""
Basel III/IV Harvester Blueprint
=================================
Harvests regulatory definitions from the Basel III Framework.
Source: Bank for International Settlements (bis.org)

Basel III defines prudential standards for banks, including capital adequacy,
liquidity, and leverage ratios. These regulatory requirements are critical
for financial metrics governance — they determine what constitutes
"regulatory capital" and how risk-weighted assets must be calculated.

Architecture: Static harvest with live BIS source URLs.
"""

from ..core import BaseHarvester, HarvesterException
from typing import Dict, Any, List


class BaselHarvester(BaseHarvester):
    """
    Harvester for Basel III/IV Framework.
    Source: bis.org (Bank for International Settlements)

    Usage:
        harvester = BaselHarvester()
        result = harvester.harvest("CET1")       # Common Equity Tier 1
        result = harvester.harvest("LCR")        # Liquidity Coverage Ratio
    """
    
    # ------------------------------------------------------------------ #
    # REGULATORY DEFINITIONS (STATIC — these are standardized by BCBS)    #
    # To add a new concept: add an entry here — zero code changes needed. #
    # ------------------------------------------------------------------ #
    DEFINITIONS: Dict[str, Dict[str, Any]] = {
        "CET1": {
            "title": "Common Equity Tier 1 Capital Ratio",
            "text": "The Common Equity Tier 1 (CET1) capital ratio is the ratio of a bank's core equity capital to its total risk-weighted assets (RWAs). CET1 capital consists of: common shares, retained earnings, other comprehensive income, qualifying minority interests, and regulatory adjustments. The minimum CET1 ratio is 4.5%, with a capital conservation buffer of 2.5%, bringing the effective minimum to 7%.",
            "framework": "Basel III — Pillar 1",
            "standard_ref": "BCBS d424 (December 2017)",
            "relevance": "Defines the denominator for financial health metrics — directly governs how ODGS financial metrics calculate capital adequacy",
            "source_url": "https://www.bis.org/bcbs/publ/d424.htm"
        },
        "LCR": {
            "title": "Liquidity Coverage Ratio",
            "text": "The Liquidity Coverage Ratio (LCR) requires banks to hold a stock of high-quality liquid assets (HQLA) sufficient to cover net cash outflows over a 30-day stress period. LCR = Stock of HQLA / Total net cash outflows over 30 days >= 100%. HQLA are classified into Level 1 (cash, central bank reserves, sovereign debt) and Level 2 assets (corporate bonds, covered bonds).",
            "framework": "Basel III — Liquidity",
            "standard_ref": "BCBS d295 (January 2013)",
            "relevance": "Liquidity risk measurement — the regulatory basis for ODGS liquidity and cash flow metrics",
            "source_url": "https://www.bis.org/publ/bcbs238.htm"
        },
        "NSFR": {
            "title": "Net Stable Funding Ratio",
            "text": "The Net Stable Funding Ratio (NSFR) requires banks to maintain a stable funding profile in relation to the composition of their assets and off-balance sheet activities. NSFR = Available Stable Funding (ASF) / Required Stable Funding (RSF) >= 100%. ASF includes capital, preferred stock, and deposits with maturities exceeding one year.",
            "framework": "Basel III — Liquidity",
            "standard_ref": "BCBS d295 (January 2013)",
            "relevance": "Long-term funding stability — governs asset-liability matching in ODGS financial process maps",
            "source_url": "https://www.bis.org/bcbs/publ/d295.htm"
        },
        "LeverageRatio": {
            "title": "Leverage Ratio",
            "text": "The leverage ratio is a non-risk-based measure defined as: Tier 1 Capital / Total Exposure Measure >= 3%. The exposure measure includes on-balance sheet items, derivatives, securities financing transactions, and off-balance sheet items. Unlike risk-weighted ratios, the leverage ratio provides a simple, transparent backstop.",
            "framework": "Basel III — Pillar 1",
            "standard_ref": "BCBS d424 (December 2017)",
            "relevance": "Capital adequacy backstop — non-risk-weighted constraint for ODGS financial stability metrics",
            "source_url": "https://www.bis.org/bcbs/publ/d424.htm"
        },
        "FRTB": {
            "title": "Fundamental Review of the Trading Book",
            "text": "FRTB introduces a revised boundary between the trading book and banking book, and a new standardised approach and internal models approach for calculating market risk capital. Key changes include: Expected Shortfall (ES) replacing Value-at-Risk (VaR), desk-level model approval, and non-modellable risk factors (NMRFs).",
            "framework": "Basel III — Market Risk",
            "standard_ref": "BCBS d457 (January 2019)",
            "relevance": "Market risk measurement standard — defines how derivatives and trading positions must be governed",
            "source_url": "https://www.bis.org/bcbs/publ/d457.htm"
        },
        "IRRBB": {
            "title": "Interest Rate Risk in the Banking Book",
            "text": "IRRBB refers to the current or prospective risk to the bank's capital and earnings arising from adverse movements in interest rates that affect banking book positions. Banks must measure the impact using Economic Value of Equity (EVE) and Net Interest Income (NII) approaches under prescribed shock scenarios.",
            "framework": "Basel III — Pillar 2",
            "standard_ref": "BCBS d368 (April 2016)",
            "relevance": "Interest rate governance — the regulatory basis for ODGS interest rate sensitivity metrics",
            "source_url": "https://www.bis.org/bcbs/publ/d368.htm"
        },
        "OpRisk": {
            "title": "Standardised Approach for Operational Risk",
            "text": "The standardised approach calculates operational risk capital using the Business Indicator Component (BIC), which combines: (1) the Interest, Leases and Dividend Component (ILDC), (2) the Services Component (SC), and (3) the Financial Component (FC). Banks with a history of operational losses must apply an Internal Loss Multiplier (ILM).",
            "framework": "Basel III — Pillar 1",
            "standard_ref": "BCBS d424 (December 2017)",
            "relevance": "Operational risk capital — governs how data quality failures in ODGS translate to regulatory capital charges",
            "source_url": "https://www.bis.org/bcbs/publ/d424.htm"
        },
    }

    @classmethod
    def list_available_concepts(cls) -> List[Dict[str, str]]:
        """List all Basel III/IV concepts available for harvesting."""
        return [
            {
                "concept": name,
                "title": info["title"],
                "framework": info["framework"],
                "standard_ref": info["standard_ref"],
                "source_url": info["source_url"]
            }
            for name, info in cls.DEFINITIONS.items()
        ]

    def harvest(self, reference_id: str) -> Dict[str, Any]:
        """
        Harvests a specific Basel III/IV regulatory definition.
        
        Args:
            reference_id: The concept name (e.g. "CET1", "LCR", "FRTB")
            
        Returns:
            Dict: SovereignDefinition
        """
        # Try exact match first, then case-insensitive
        concept = self.DEFINITIONS.get(reference_id)
        if not concept:
            for key, value in self.DEFINITIONS.items():
                if key.lower() == reference_id.lower():
                    concept = value
                    reference_id = key
                    break
        
        if not concept:
            available = ", ".join(self.DEFINITIONS.keys())
            raise HarvesterException(
                f"Basel concept '{reference_id}' is not in the harvest registry.\n"
                f"  Available concepts: {available}\n"
                f"  To add more concepts, update DEFINITIONS in basel.py — zero code changes needed."
            )
        
        urn = f"urn:odgs:def:bis:basel3:{reference_id.lower()}:v2024"
        
        definition = {
            "urn": urn,
            "metadata": {
                "authority_id": "BIS_BCBS",
                "authority_name": "Bank for International Settlements — Basel Committee on Banking Supervision",
                "document_ref": concept["standard_ref"],
                "source_uri": concept["source_url"],
                "hierarchy": {
                    "level": "regulatory_definition",
                    "framework": concept["framework"],
                    "local_id": reference_id
                }
            },
            "relations": [],
            "content": {
                "verbatim_text": concept["text"],
                "title": concept["title"],
                "language": "en",
                "format": "TEXT",
                "structured_data": {
                    "standard": "Basel III",
                    "concept": reference_id,
                    "framework_area": concept["framework"],
                    "standard_reference": concept["standard_ref"],
                    "relevance_to_odgs": concept["relevance"]
                }
            },
            "interpretation": {
                "summary": f"Basel III: {concept['title']}",
                "applicability": "Banking and Financial Institutions"
            }
        }
        
        return definition
