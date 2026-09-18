from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawQuote:
    """One price observation from one provider, before consensus is computed."""
    source_id: str
    publisher: str
    commodity: str
    price: float
    currency: str
    unit: str
    as_of: datetime          # when the PROVIDER says this price was true
    retrieved_at: datetime   # when WE fetched it


class SourceError(Exception):
    """A provider failed to give us a clean quote. Must always be raised, never swallowed."""

    def __init__(self, source_id: str, reason: str):
        self.source_id = source_id
        self.reason = reason
        super().__init__(f"[{source_id}] {reason}")
