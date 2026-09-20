"""Data models for corpus records and search results."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Source integration type."""
    LOCAL_OPTIONAL = "local_optional"
    REMOTE_ONLY = "remote_only"
    PLANNED_ADAPTER = "planned_adapter"
    DEFERRED = "deferred"


class AccessStatus(str, Enum):
    """Current integration access status."""
    LOCAL_CONFIGURED = "local_configured"
    LOCAL_NOT_CONFIGURED = "local_not_configured"
    REMOTE_STATUS_ONLY = "remote_status_only"
    NOT_READY = "not_ready"
    DEFERRED = "deferred"
    ADAPTER_READY = "adapter_ready"


class CorpusRecord(BaseModel):
    """Registry entry for a single ancient text corpus."""
    corpus_id: str
    name: str
    languages: list[str]
    period: str
    source_type: SourceType
    access_status: AccessStatus
    source_url: str
    licence: str
    licence_notes: str = ""
    integration_notes: str = ""


class ProvenanceEnvelope(BaseModel):
    """Provenance metadata attached to every result."""
    source_layer: str
    corpus_id: str
    source_url: str
    licence: str
    licence_warning: str = ""
    access_status: str


class SearchResult(BaseModel):
    """Structured search result or status response."""
    provenance: ProvenanceEnvelope
    status: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    message: str = ""


class TextResult(BaseModel):
    """Structured text retrieval result."""
    provenance: ProvenanceEnvelope
    status: str
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
