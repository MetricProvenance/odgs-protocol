from __future__ import annotations
from typing import List, Optional, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
import re
from datetime import datetime

class HierarchyLevel(str, Enum):
    DOCUMENT = "document"
    CHAPTER = "chapter"
    SECTION = "section"
    ARTICLE = "article"
    PARAGRAPH = "paragraph"
    CONCEPT = "concept"

class RelationType(str, Enum):
    SUB_CLASS_OF = "subClassOf"
    PART_OF = "partOf"
    IS_DEFINED_BY = "isDefinedBy"
    RELATED_TO = "relatedTo"

class ContentFormat(str, Enum):
    TEXT = "TEXT"
    XML_FRAGMENT = "XML_FRAGMENT"
    JSON_LD = "JSON_LD"
    MARKDOWN = "MARKDOWN"

class SovereignHierarchy(BaseModel):
    level: HierarchyLevel
    parent_ref: Optional[str] = None
    local_id: Optional[str] = None

class SovereignMetadata(BaseModel):
    authority_id: str = Field(..., description="e.g. NL_GOV, AI_SYNTHETIC")
    authority_name: str
    document_ref: str
    harvested_at: datetime = Field(default_factory=datetime.now)
    source_uri: Optional[str] = None
    content_hash: Optional[str] = Field(None, description="SHA-256 of verbatim_text")
    hierarchy: Optional[SovereignHierarchy] = None

    @model_validator(mode='after')
    def enforce_provenance(self) -> 'SovereignMetadata':
        """EU AI Act Art. 10: non-synthetic definitions must record origin and integrity hash."""
        if self.authority_id != "AI_SYNTHETIC":
            if self.source_uri is None:
                raise ValueError(
                    f"source_uri is required for authority '{self.authority_id}' "
                    "(EU AI Act Art. 10 — data provenance). Use authority_id='AI_SYNTHETIC' to exempt."
                )
            if self.content_hash is None:
                raise ValueError(
                    f"content_hash is required for authority '{self.authority_id}' "
                    "(EU AI Act Art. 10 — integrity). Provide a SHA-256 hash of verbatim_text."
                )
        return self

class SovereignRelation(BaseModel):
    type: RelationType
    target_urn: str

class StructuredDataItem(BaseModel):
    key: str
    value: str

class SovereignContent(BaseModel):
    verbatim_text: str
    language: str = "en-US"
    format: ContentFormat = ContentFormat.TEXT
    structured_data: Optional[List[StructuredDataItem]] = None

class SovereignInterpretation(BaseModel):
    summary: str
    applicability: str

class SovereignDefinition(BaseModel):
    """
    The Sovereign Definition (v3.2)
    Strict implementation of lib/schemas/sovereign/01-definitions-schema.json
    """
    urn: str = Field(..., pattern=r"^urn:odgs:def:[a-z0-9_]+:[a-z0-9_]+:v[0-9.]+$")
    metadata: SovereignMetadata
    relations: List[SovereignRelation] = Field(default_factory=list)
    content: SovereignContent
    interpretation: Optional[SovereignInterpretation] = None

    @field_validator('urn')
    def validate_urn_format(cls, v):
        if not re.match(r"^urn:odgs:def:[a-z0-9_]+:[a-z0-9_]+:v[0-9.]+$", v):
            raise ValueError('URN must match format: urn:odgs:def:<authority>:<external_id>:<version>')
        return v
