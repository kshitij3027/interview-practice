from __future__ import annotations

from .io import Dataset


class VelocityResolver:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def resolve_all(self) -> list[dict]:
        raise NotImplementedError("resolve_all must be implemented")
