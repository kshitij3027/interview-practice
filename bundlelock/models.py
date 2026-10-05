from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> "Version":
        if not isinstance(raw, str) or not raw:
            raise ValueError("invalid version")
        parts = raw.split(".")
        if len(parts) != 3:
            raise ValueError("invalid version")
        values: list[int] = []
        for part in parts:
            if not part.isdigit() or (len(part) > 1 and part[0] == "0"):
                raise ValueError("invalid version")
            values.append(int(part))
        return cls(*values)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class Release:
    package_id: str
    version: Version
    channel: str
    artifact_mb: int


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    package_id: str
    version: Version
    requires_package_id: str
    min_version: Version
    max_version_exclusive: Version

    def accepts(self, version: Version) -> bool:
        return self.min_version <= version < self.max_version_exclusive


@dataclass(frozen=True)
class TargetRequirement:
    package_id: str
    min_version: Version
    max_version_exclusive: Version

    def accepts(self, version: Version) -> bool:
        return self.min_version <= version < self.max_version_exclusive
