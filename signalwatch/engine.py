"""Customer incident screening capability."""
from .catalog import Catalog
from .requests import Event


class SignatureScreen:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def evaluate(self, event: Event) -> dict:
        raise NotImplementedError("signature screening is not implemented in the starter")
