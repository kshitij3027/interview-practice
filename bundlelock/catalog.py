from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass

from .models import Dependency, Release, Version


@dataclass(frozen=True)
class Catalog:
    packages: dict[str, str]
    releases_by_package: dict[str, tuple[Release, ...]]
    releases: dict[tuple[str, Version], Release]
    dependencies_by_release: dict[tuple[str, Version], tuple[Dependency, ...]]
    installed: dict[str, Version]

    @classmethod
    def load(cls, packages_path, versions_path, dependencies_path, installed_path):
        packages = _load_packages(packages_path)
        releases, by_package = _load_releases(versions_path, packages)
        dependencies = _load_dependencies(dependencies_path, packages, releases)
        installed = _load_installed(installed_path, packages, releases)
        return cls(
            packages=packages,
            releases_by_package={k: tuple(sorted(v, key=lambda r: r.version)) for k, v in by_package.items()},
            releases=releases,
            dependencies_by_release={k: tuple(sorted(v, key=lambda d: d.dependency_id)) for k, v in dependencies.items()},
            installed=installed,
        )

    def dependency_count(self) -> int:
        return sum(len(v) for v in self.dependencies_by_release.values())


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing {field}")
    return value


def _load_packages(path):
    packages = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            package_id = _required(row, "package_id")
            if package_id in packages:
                raise ValueError(f"duplicate package_id: {package_id}")
            packages[package_id] = _required(row, "display_name")
    if not packages:
        raise ValueError("empty package catalog")
    return packages


def _load_releases(path, packages):
    releases = {}
    by_package = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            package_id = _required(row, "package_id")
            if package_id not in packages:
                raise ValueError(f"unknown release package: {package_id}")
            version = Version.parse(_required(row, "version"))
            channel = _required(row, "channel")
            if channel not in {"stable", "canary"}:
                raise ValueError("invalid channel")
            try:
                artifact_mb = int(_required(row, "artifact_mb"))
            except ValueError as exc:
                raise ValueError("invalid artifact_mb") from exc
            if artifact_mb <= 0:
                raise ValueError("artifact_mb must be positive")
            key = (package_id, version)
            if key in releases:
                raise ValueError(f"duplicate release: {package_id}@{version}")
            release = Release(package_id, version, channel, artifact_mb)
            releases[key] = release
            by_package[package_id].append(release)
    for package_id in packages:
        if package_id not in by_package:
            raise ValueError(f"package has no releases: {package_id}")
    return releases, by_package


def _load_dependencies(path, packages, releases):
    result = defaultdict(list)
    seen = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            dep_id = _required(row, "dependency_id")
            package_id = _required(row, "package_id")
            version = Version.parse(_required(row, "version"))
            required = _required(row, "requires_package_id")
            minimum = Version.parse(_required(row, "min_version"))
            maximum = Version.parse(_required(row, "max_version_exclusive"))
            if minimum >= maximum:
                raise ValueError(f"invalid dependency range: {dep_id}")
            if package_id not in packages or required not in packages:
                raise ValueError(f"unknown package reference: {dep_id}")
            if (package_id, version) not in releases:
                raise ValueError(f"unknown declaring release: {dep_id}")
            dep = Dependency(dep_id, package_id, version, required, minimum, maximum)
            if dep_id in seen:
                if seen[dep_id] != dep:
                    raise ValueError(f"conflicting dependency_id: {dep_id}")
                continue
            seen[dep_id] = dep
            result[(package_id, version)].append(dep)
    return result


def _load_installed(path, packages, releases):
    installed = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            package_id = _required(row, "package_id")
            version = Version.parse(_required(row, "version"))
            if package_id not in packages or (package_id, version) not in releases:
                raise ValueError(f"unknown installed release: {package_id}@{version}")
            if package_id in installed:
                raise ValueError(f"duplicate installed package: {package_id}")
            installed[package_id] = version
    return installed
