from ..core import BaseHarvester, HarvesterException
import urllib.request
import ssl
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional


def _local_tag(element) -> str:
    """Extract the local tag name from a possibly namespaced XML element."""
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[-1]
    return tag


class AwBHarvester(BaseHarvester):
    """
    Harvester for the Dutch 'Algemene wet bestuursrecht' (AwB).
    Source: wetten.overheid.nl
    """
    
    # Official Repository link for a specific version (2024-01-01)
    BASE_URL = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0005537/2024-01-01_0/xml/BWBR0005537_2024-01-01_0.xml"

    def harvest(self, reference_id: str, target_metric_urn: Optional[str] = None) -> Dict[str, Any]:
        """
        Harvests a specific Article from the AwB.
        
        Args:
            reference_id: The Article Label (e.g. "1:3")
            target_metric_urn: Optional URN of the metric this definition maps to.
                               If None, no metric relation is added.
            
        Returns:
            Dict: SovereignDefinition
        """
        print(f"Fetching AwB XML from {self.BASE_URL}...")
        try:
            ssl_ctx = ssl.create_default_context()
            with urllib.request.urlopen(self.BASE_URL, context=ssl_ctx, timeout=30) as response:
                xml_data = response.read()
        except Exception as e:
            raise HarvesterException(f"Failed to fetch AwB XML: {e}")

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
             raise HarvesterException(f"Failed to parse AwB XML: {e}")

        # Find the Article — search all elements whose local tag is "artikel"
        # The XML may use namespaces (e.g. {bwb-dl1.0}artikel), so we compare
        # local names rather than full qualified tags.
        target_article = None
        target_label = reference_id if reference_id.startswith("Artikel ") else f"Artikel {reference_id}"
        
        for elem in root.iter():
            if _local_tag(elem) == "artikel" and elem.get("label") == target_label:
                target_article = elem
                break
        
        if target_article is None:
            raise HarvesterException(f"Article {reference_id} not found in AwB.")

        # Extract Text — iterate children using namespace-agnostic local tags
        lid_texts = []
        full_text = ""
        
        for child in target_article:
            local = _local_tag(child)
            if local == "lid":
                # The lid number element is "lidnr" (not "lidnummer") in the AwB XML
                lid_num = None
                inhoud = None
                for sub in child:
                    sub_local = _local_tag(sub)
                    if sub_local in ("lidnr", "lidnummer"):
                        lid_num = "".join(sub.itertext()).strip()
                    elif sub_local in ("inhoud", "al"):
                        inhoud = sub
                
                # Get only the actual content, not the lidnr number text
                if inhoud is not None:
                    text_content = "".join(inhoud.itertext()).strip()
                    # The inhoud may start with the lid number again — strip it
                    if lid_num and text_content.startswith(lid_num):
                        text_content = text_content[len(lid_num):].strip()
                else:
                    # Fallback: extract text from lid, skipping the lidnr sub-element
                    parts = []
                    for sub in child:
                        sub_local = _local_tag(sub)
                        if sub_local not in ("lidnr", "lidnummer"):
                            parts.append("".join(sub.itertext()).strip())
                    text_content = " ".join(p for p in parts if p)
                
                lid_label = f"Lid {lid_num}" if lid_num else "Lid"
                if text_content:
                    lid_texts.append(f"{lid_label}: {text_content}")
            elif local == "kop":
                pass  # Title — skip
            elif local in ("inhoud", "al"):
                # Article-level content (no lid structure)
                text_content = "".join(child.itertext()).strip()
                if text_content:
                    lid_texts.append(text_content)

        full_text = "\n".join(lid_texts)
        if not full_text:
             # Final fallback: extract all text from the article element
             full_text = "".join(target_article.itertext()).strip()

        # Construct SovereignDefinition
        urn = f"urn:odgs:def:nl_gov:awb:art_{reference_id.replace(':', '_')}:v2024"
        
        # Build relations — only add metric link if explicitly provided
        relations = []
        if target_metric_urn:
            relations.append({
                "type": "isDefinedBy",
                "target_urn": target_metric_urn
            })

        definition = {
            "urn": urn,
            "metadata": {
                "authority_id": "NL_GOV",
                "authority_name": "Government of the Netherlands",
                "document_ref": "Algemene wet bestuursrecht (AwB)",
                "source_uri": f"{self.BASE_URL}#art_{reference_id}",
                "hierarchy": {
                    "level": "article",
                    "parent_ref": "AwB",
                    "local_id": reference_id
                }
            },
            "relations": relations,
            "content": {
                "verbatim_text": full_text,
                "language": "nl-NL",
                "format": "XML_FRAGMENT",
                "structured_data": {} 
            },
            "interpretation": {
                "summary": f"Auto-harvested definition — AwB Artikel {reference_id}.",
                "applicability": "General Administrative Law"
            }
        }
        
        return definition
