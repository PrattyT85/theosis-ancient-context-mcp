"""Adapter registry — resolves corpus ID to adapter instance."""
from __future__ import annotations

from .cdli import CDLIAdapter
from .coptic import CopticScriptoriumAdapter
from .cuc import CUCAdapter
from .remote_status import (
    DASIAdapter,
    DeferredAdapter,
    HPMAdapter,
    OCIANAAdapter,
    TLAAdapter,
)


def get_adapter(corpus_id: str):
    """Return the adapter for a corpus ID, or None if unknown."""
    _ADAPTERS = {
        "tla": TLAAdapter(),
        "coptic_scriptorium": CopticScriptoriumAdapter(),
        "hpm_hdivt": HPMAdapter(),
        "cuc": CUCAdapter(),
        "dasi": DASIAdapter(),
        "ociana": OCIANAAdapter(),
        "cdli": CDLIAdapter(),
        "dppc": DeferredAdapter("dppc"),
        "cip": DeferredAdapter("cip"),
    }
    return _ADAPTERS.get(corpus_id)
