"""Source-separated discovery and a frozen complete coordinate family.

The separation check compares declared primitive identifiers. It cannot discover
an omitted shared shock or establish independence of the primitives themselves.
No routine in this module accepts evaluation outcomes or oracle targets.
"""

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Hashable, Iterable, Mapping

import numpy as np

from comet.queries import SignedQuery


def check_source_separation(split_sources: Mapping[str, Iterable[Hashable]]) -> dict:
    """Verify disjoint declared training/discovery/certification source sets.

    Identifiers must be globally qualified, e.g. ``(namespace, primitive_id)``;
    equal bare row numbers are not evidence of equal or independent sources.
    """
    required = {"training", "discovery", "certification"}
    if not required <= split_sources.keys():
        raise ValueError("declare training, discovery and certification source sets")
    try:
        sources = {name: frozenset(values) for name, values in split_sources.items()}
    except TypeError as exc:
        raise ValueError("source identifiers must be globally qualified hashable values") from exc
    names = sorted(sources)
    for index, name in enumerate(names):
        for other in names[index + 1 :]:
            if not sources[name].isdisjoint(sources[other]):
                raise ValueError(f"SOURCE_LEAKAGE: declared sources overlap between {name} and {other}")
    return {
        "status": "DECLARED_SOURCE_SETS_DISJOINT",
        "source_counts": {name: len(sources[name]) for name in names},
        "scope": "declared identifiers only; hidden sources and primitive independence are model assumptions",
    }


def _coordinate_hash(query: SignedQuery) -> str:
    digest = hashlib.sha256()
    header = {
        "schema": "signed-coordinate-v1",
        "shape": query.coefficients.shape,
        "channel": query.channel,
        "normalizer": query.normalizer.hex(),
    }
    digest.update(json.dumps(header, sort_keys=True, separators=(",", ":")).encode())
    for array in (query.coefficients, query.offset):
        # Signed zero has no effect on a linear coordinate and is canonicalized.
        canonical = np.where(array == 0, 0.0, array).astype("<f8", copy=False)
        digest.update(canonical.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class FrozenFamily:
    queries: tuple[SignedQuery, ...]
    aliases: Mapping[str, str]
    coordinate_hashes: Mapping[str, str]
    digest: str

    @property
    def family_size(self) -> int:
        return len(self.queries)

    def canonical_id(self, query_id: str) -> str:
        try:
            return self.aliases[query_id]
        except KeyError as exc:
            raise ValueError(f"coordinate {query_id!r} is outside the frozen family") from exc


def freeze_discovered_family(queries: Iterable[SignedQuery]) -> FrozenFamily:
    """Deduplicate exact risk AND utility coordinates before assigning m.

    The first occurrence supplies the canonical identifier. Distinct channels
    or normalizers remain distinct even when their coefficient bytes agree.
    Hashing freezes a declaration; source separation must be established before
    conditioning on this family. A digest cannot prove absence of outcome tuning.
    """
    unique: list[SignedQuery] = []
    aliases: dict[str, str] = {}
    hashes: dict[str, str] = {}
    by_hash: dict[str, str] = {}
    all_id_hashes: dict[str, str] = {}
    n_rows = None
    for query in queries:
        if not isinstance(query, SignedQuery):
            raise ValueError("the discovered family must contain SignedQuery values")
        if n_rows is None:
            n_rows = query.n_rows
        if query.n_rows != n_rows:
            raise ValueError("one frozen family must share a fixed row design")
        coordinate_hash = _coordinate_hash(query)
        if query.query_id in all_id_hashes and all_id_hashes[query.query_id] != coordinate_hash:
            raise ValueError("one query_id cannot identify two different coordinates")
        all_id_hashes[query.query_id] = coordinate_hash
        if coordinate_hash not in by_hash:
            by_hash[coordinate_hash] = query.query_id
            hashes[query.query_id] = coordinate_hash
            unique.append(query)
        aliases[query.query_id] = by_hash[coordinate_hash]
    if not unique:
        raise ValueError("a frozen decision family must contain at least one coordinate")
    header = {
        "schema": "frozen-discovered-family-v1",
        "coordinates": [(query.query_id, hashes[query.query_id]) for query in unique],
        "aliases": aliases,
    }
    digest = hashlib.sha256(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return FrozenFamily(tuple(unique), MappingProxyType(aliases), MappingProxyType(hashes), digest)
