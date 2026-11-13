"""Serial-recovery capability. Your implementation belongs here or in supporting modules."""
from __future__ import annotations

from .catalog import Catalog
from .contracts import Scan


class SerialRecovery:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def recover(self, scan: Scan) -> dict:
        return {
            "scan_id": scan.scan_id,
            "status": "not_implemented",
            "serial": None,
            "penalty": None,
            "ambiguous": False,
        }
