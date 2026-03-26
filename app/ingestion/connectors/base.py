"""
Abstract base class for all data source connectors.

Every connector must implement:
  - ``test_connection()`` — verify credentials without fetching data
  - ``get_schema()`` — return available tables/objects
  - ``extract()`` — yield batches of records

Adapted from DataClean's ingestion/connectors/base.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator


class BaseConnector(ABC):
    """
    Abstract source connector.

    Parameters
    ----------
    config: dict of connector-specific settings (credentials, URLs, etc.)
    """

    def __init__(self, config: dict) -> None:
        self.config = config

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Identifier string, e.g. 'sage_intacct', 'csv'."""

    @abstractmethod
    def test_connection(self) -> dict:
        """
        Verify connectivity without fetching data.

        Returns
        -------
        dict with keys: ok (bool), message (str), latency_ms (int).
        """

    @abstractmethod
    def get_schema(self) -> list[dict]:
        """
        Return available objects/tables in the source.

        Returns
        -------
        List of dicts with keys: name, description, estimated_rows.
        """

    @abstractmethod
    def extract(
        self,
        object_name: str,
        watermark: str | None = None,
        batch_size: int = 1000,
    ) -> Generator[list[dict], None, None]:
        """
        Yield batches of records for *object_name*.

        Parameters
        ----------
        object_name:  Table/object to extract (as returned by get_schema()).
        watermark:    ISO-8601 datetime string for incremental extraction.
                      None = full extract.
        batch_size:   Rows per yielded batch.
        """
