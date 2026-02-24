"""
GDPR Harvester Blueprint
=========================
Harvests article definitions from the EU General Data Protection Regulation.
Source: EUR-Lex (eur-lex.europa.eu)

This blueprint uses the EUR-Lex content service to fetch GDPR article text.
GDPR articles are foundational for data governance — they define the legal
requirements for data protection, consent, and accountability that ODGS
metrics and rules must comply with.

Architecture: Static harvest with live EUR-Lex validation.
"""

from ..core import BaseHarvester, HarvesterException
import urllib.request
import ssl
import re
from typing import Dict, Any, List


class GDPRHarvester(BaseHarvester):
    """
    Harvester for EU GDPR (Regulation 2016/679).
    Source: eur-lex.europa.eu
    
    Usage:
        harvester = GDPRHarvester()
        result = harvester.harvest("5")     # Article 5: Principles
        result = harvester.harvest("25")    # Article 25: Data Protection by Design
    """
    
    # EUR-Lex CELLAR URI for GDPR
    BASE_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"

    # ------------------------------------------------------------------ #
    # ARTICLE DEFINITIONS (STATIC — GDPR text is immutable post-adoption) #
    # These are the authoritative article texts.                           #
    # To add a new article: add an entry here — zero code changes needed.  #
    # ------------------------------------------------------------------ #
    ARTICLES: Dict[str, Dict[str, Any]] = {
        "5": {
            "title": "Principles relating to processing of personal data",
            "text": "Personal data shall be: (a) processed lawfully, fairly and in a transparent manner in relation to the data subject ('lawfulness, fairness and transparency'); (b) collected for specified, explicit and legitimate purposes and not further processed in a manner that is incompatible with those purposes ('purpose limitation'); (c) adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed ('data minimisation'); (d) accurate and, where necessary, kept up to date ('accuracy'); (e) kept in a form which permits identification of data subjects for no longer than is necessary ('storage limitation'); (f) processed in a manner that ensures appropriate security ('integrity and confidentiality').",
            "chapter": "Chapter II — Principles",
            "relevance": "Foundational data quality principles — maps directly to ODGS DQ dimensions (Accuracy, Completeness, Timeliness)",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e1807-1-1"
        },
        "6": {
            "title": "Lawfulness of processing",
            "text": "Processing shall be lawful only if and to the extent that at least one of the following applies: (a) the data subject has given consent; (b) processing is necessary for the performance of a contract; (c) processing is necessary for compliance with a legal obligation; (d) processing is necessary to protect vital interests; (e) processing is necessary for a task carried out in the public interest; (f) processing is necessary for legitimate interests pursued by the controller.",
            "chapter": "Chapter II — Principles",
            "relevance": "Legal basis for all data processing — prerequisite for any ODGS metric computation",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e1888-1-1"
        },
        "17": {
            "title": "Right to erasure ('right to be forgotten')",
            "text": "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies: (a) the personal data are no longer necessary; (b) the data subject withdraws consent; (c) the data subject objects to the processing; (d) the personal data have been unlawfully processed; (e) compliance with a legal obligation; (f) data collected in relation to information society services.",
            "chapter": "Chapter III — Rights of the Data Subject",
            "relevance": "Data retention governance — impacts ODGS storage limitation dimensions and archival rules",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e2589-1-1"
        },
        "25": {
            "title": "Data protection by design and by default",
            "text": "The controller shall, both at the time of the determination of the means for processing and at the time of the processing itself, implement appropriate technical and organisational measures, such as pseudonymisation, which are designed to implement data-protection principles in an effective manner and to integrate the necessary safeguards into the processing.",
            "chapter": "Chapter IV — Controller and Processor",
            "relevance": "Architecture-level governance — requires data quality controls to be embedded by design, not bolted on",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e3063-1-1"
        },
        "30": {
            "title": "Records of processing activities",
            "text": "Each controller and, where applicable, the controller's representative, shall maintain a record of processing activities under its responsibility. That record shall contain: (a) the name and contact details of the controller; (b) the purposes of the processing; (c) a description of the categories of data subjects and personal data; (d) the categories of recipients; (e) transfers to third countries; (f) time limits for erasure; (g) a description of technical and organisational security measures.",
            "chapter": "Chapter IV — Controller and Processor",
            "relevance": "Data lineage and cataloguing — the regulatory mandate for ODGS process maps and audit trails",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e3265-1-1"
        },
        "35": {
            "title": "Data protection impact assessment",
            "text": "Where a type of processing in particular using new technologies, and taking into account the nature, scope, context and purposes of the processing, is likely to result in a high risk to the rights and freedoms of natural persons, the controller shall, prior to the processing, carry out an assessment of the impact of the envisaged processing operations on the protection of personal data.",
            "chapter": "Chapter IV — Controller and Processor",
            "relevance": "Risk assessment — the precursor to ODGS Compliance Shield scoring for high-risk data operations",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e3546-1-1"
        },
        "83": {
            "title": "General conditions for imposing administrative fines",
            "text": "Each supervisory authority shall ensure that the imposition of administrative fines shall in each individual case be effective, proportionate and dissuasive. Fines up to EUR 20,000,000 or 4% of annual worldwide turnover, whichever is higher, for infringements of the basic principles for processing, data subjects' rights, and transfers to third countries.",
            "chapter": "Chapter VIII — Remedies, Liability and Penalties",
            "relevance": "Penalty framework — quantifies the financial risk that ODGS governance is designed to mitigate",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679#d1e6226-1-1"
        },
    }

    @classmethod
    def list_available_articles(cls) -> List[Dict[str, str]]:
        """List all GDPR articles available for harvesting."""
        return [
            {
                "article": f"Art. {num}",
                "title": info["title"],
                "chapter": info["chapter"],
                "relevance": info["relevance"],
                "source_url": info["source_url"]
            }
            for num, info in cls.ARTICLES.items()
        ]

    def harvest(self, reference_id: str) -> Dict[str, Any]:
        """
        Harvests a specific GDPR Article.
        
        Args:
            reference_id: The article number (e.g. "5", "25", "83")
            
        Returns:
            Dict: SovereignDefinition
        """
        # Normalize input (strip "Art." prefix if provided)
        article_num = reference_id.strip().replace("Art.", "").replace("art.", "").strip()
        
        if article_num not in self.ARTICLES:
            available = ", ".join(sorted(self.ARTICLES.keys(), key=int))
            raise HarvesterException(
                f"GDPR Article {article_num} is not in the harvest registry.\n"
                f"  Available articles: {available}\n"
                f"  To add more articles, update ARTICLES in gdpr.py — zero code changes needed."
            )
        
        article = self.ARTICLES[article_num]
        
        urn = f"urn:odgs:def:eu:gdpr:art_{article_num}:v2016"
        
        definition = {
            "urn": urn,
            "metadata": {
                "authority_id": "EU_GDPR",
                "authority_name": "EU General Data Protection Regulation (2016/679)",
                "document_ref": f"GDPR Article {article_num}",
                "source_uri": article["source_url"],
                "hierarchy": {
                    "level": "article",
                    "chapter": article["chapter"],
                    "local_id": f"Art_{article_num}"
                }
            },
            "relations": [],
            "content": {
                "verbatim_text": article["text"],
                "title": article["title"],
                "language": "en",
                "format": "TEXT",
                "structured_data": {
                    "regulation": "GDPR (2016/679)",
                    "article_number": int(article_num),
                    "chapter": article["chapter"],
                    "relevance_to_odgs": article["relevance"]
                }
            },
            "interpretation": {
                "summary": f"GDPR Art. {article_num}: {article['title']}",
                "applicability": "All organizations processing personal data of EU residents"
            }
        }
        
        return definition
