#!/usr/bin/env python3
"""Audit published DANDI manifests for nested items lacking a ``name``.

Motivation: https://github.com/dandi/dandi-schema/issues/442 proposes making
``name`` required on ``Contributor`` (hence ``Organization``), ``BaseType``
subclasses (``Anatomy``, ``SpeciesType``, ...) and possibly other classes whose
``name`` is currently ``Optional``.  Before doing so we need to know which
already *published* (immutable) versions would turn from valid to invalid.

The script walks the public S3 manifests of a DANDI instance
(``dandisets/<id>/<version>/dandiset.jsonld`` and, optionally,
``assets.jsonld``) without authentication, and for every nested object whose
``schemaKey`` belongs to a class with an optional ``name`` it reports:

* ``missing``  -- ``name`` absent or ``null``  (breaks with ``name: str``)
* ``empty``    -- ``name`` is ``""`` or only whitespace (would break only if we
  also add ``min_length=1`` / a non-blank pattern)

together with whether the object carries an ``identifier`` (i.e. whether the
alternative "``name`` OR ``identifier``" rule would still accept it).

To tell "valid -> invalid" apart from "already invalid", each Dandiset record is
also migrated to the current schema version and validated with the *installed*
``dandischema`` (``--no-validate`` to skip).  Run it with ``dandischema`` from
``master`` to get the baseline; the verdict ``WOULD_BREAK`` means the record
validates today but contains at least one ``missing`` name.

Examples
--------
Quick look at a few Dandisets::

    python tools/audit_nameless_items.py --dandiset 000003 --dandiset 000026

Full audit of published Dandiset-level metadata, cached for re-runs::

    python tools/audit_nameless_items.py --cache-dir ~/.cache/dandi-audit \\
        --jobs 16 --output audit.jsonl

Include asset-level metadata (downloads can be large; see ``--max-assets-mb``)::

    python tools/audit_nameless_items.py --assets --output audit.jsonl
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from xml.etree import ElementTree

import requests

# Published records use "DANDI:<id>" identifiers; the models pick the instance
# config up at import time, so it has to be in place before importing them.
os.environ.setdefault("DANDI_INSTANCE_NAME", "DANDI")

from pydantic import BaseModel, ValidationError  # noqa: E402

from dandischema import models  # noqa: E402
from dandischema.consts import DANDI_SCHEMA_VERSION  # noqa: E402
from dandischema.metadata import migrate  # noqa: E402

DEFAULT_BUCKET_URL = "https://dandiarchive.s3.amazonaws.com"
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
VERSION_RE = re.compile(r"^\d+\.\d{6}\.\d{4}$")

# Top-level records for which an optional ``name`` is by design (assets are
# identified by path; ``CommonModel`` is only an abstract base).
EXCLUDED_CLASSES = {"CommonModel", "BareAsset", "Asset"}


@dataclass
class Finding:
    schema_key: str
    path: str
    kind: str  # "missing" | "empty"
    has_identifier: bool
    identifier: Optional[str] = None


@dataclass
class VersionReport:
    dandiset: str
    version: str
    schema_version: Optional[str] = None
    valid_now: Optional[bool] = None
    validation_error: Optional[str] = None
    findings: List[Finding] = field(default_factory=list)
    asset_findings: List[Finding] = field(default_factory=list)
    assets_scanned: Optional[int] = None
    assets_skipped_reason: Optional[str] = None
    fetch_error: Optional[str] = None

    @property
    def verdict(self) -> str:
        if self.fetch_error:
            return "FETCH_ERROR"
        missing = any(f.kind == "missing" for f in self.findings)
        if not missing:
            return "OK_EMPTY_ONLY" if self.findings else "OK"
        if self.valid_now is None:
            return "HAS_MISSING"
        return "WOULD_BREAK" if self.valid_now else "ALREADY_INVALID"


def optional_name_schema_keys() -> Set[str]:
    """``schemaKey`` values of models whose ``name`` field is optional."""
    keys: Set[str] = set()
    for obj in vars(models).values():
        if not (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj.__module__ == models.__name__
            and obj.__name__ not in EXCLUDED_CLASSES
        ):
            continue
        fields = obj.model_fields
        if "name" not in fields or fields["name"].is_required():
            continue
        default = fields["schemaKey"].default if "schemaKey" in fields else None
        keys.add(default if isinstance(default, str) else obj.__name__)
    return keys


def scan(obj: Any, targets: Set[str], path: str = "") -> Iterator[Finding]:
    """Yield findings for nested dicts with a targeted ``schemaKey``."""
    if isinstance(obj, dict):
        key = obj.get("schemaKey")
        if path and key in targets:
            name = obj.get("name")
            kind = None
            if name is None:
                kind = "missing"
            elif isinstance(name, str) and not name.strip():
                kind = "empty"
            if kind:
                ident = obj.get("identifier")
                yield Finding(
                    schema_key=key,
                    path=path,
                    kind=kind,
                    has_identifier=bool(ident),
                    identifier=str(ident) if ident else None,
                )
        for k, v in obj.items():
            yield from scan(v, targets, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from scan(v, targets, f"{path}[{i}]")


class Fetcher:
    def __init__(self, bucket_url: str, cache_dir: Optional[Path]) -> None:
        self.bucket_url = bucket_url.rstrip("/")
        self.cache_dir = cache_dir
        self.session = requests.Session()

    def list_prefixes(self, prefix: str) -> List[str]:
        out: List[str] = []
        token: Optional[str] = None
        while True:
            params = {"list-type": "2", "prefix": prefix, "delimiter": "/"}
            if token:
                params["continuation-token"] = token
            r = self.session.get(self.bucket_url + "/", params=params, timeout=60)
            r.raise_for_status()
            root = ElementTree.fromstring(r.content)
            for p in root.findall("s3:CommonPrefixes/s3:Prefix", S3_NS):
                assert p.text is not None
                out.append(p.text[len(prefix) :].rstrip("/"))
            if root.findtext("s3:IsTruncated", namespaces=S3_NS) != "true":
                return out
            token = root.findtext("s3:NextContinuationToken", namespaces=S3_NS)

    def size(self, key: str) -> Optional[int]:
        r = self.session.head(f"{self.bucket_url}/{key}", timeout=60)
        if r.status_code != 200:
            return None
        return int(r.headers.get("Content-Length", 0))

    def get_json(self, key: str) -> Any:
        cached = self.cache_dir / key if self.cache_dir else None
        if cached is not None and cached.exists():
            return json.loads(cached.read_bytes())
        r = self.session.get(f"{self.bucket_url}/{key}", timeout=600)
        r.raise_for_status()
        if cached is not None:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(r.content)
        return r.json()


def validate_now(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a Dandiset record with the installed ``dandischema``."""
    try:
        migrated = migrate(meta, to_version=DANDI_SCHEMA_VERSION, skip_validation=True)
        models.Dandiset.model_validate(migrated)
    except ValidationError as e:
        errs = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()
        )
        return False, errs[:2000]
    except Exception as e:  # migration failures etc.
        return False, f"{type(e).__name__}: {e}"[:2000]
    return True, None


def audit_version(
    fetcher: Fetcher,
    dandiset: str,
    version: str,
    targets: Set[str],
    do_validate: bool,
    do_assets: bool,
    max_assets_mb: float,
) -> VersionReport:
    rep = VersionReport(dandiset=dandiset, version=version)
    base = f"dandisets/{dandiset}/{version}"
    try:
        meta = fetcher.get_json(f"{base}/dandiset.jsonld")
    except Exception as e:
        rep.fetch_error = f"{type(e).__name__}: {e}"
        return rep
    rep.schema_version = meta.get("schemaVersion")
    rep.findings = list(scan(meta, targets))
    if do_validate:
        rep.valid_now, rep.validation_error = validate_now(meta)
    if do_assets:
        key = f"{base}/assets.jsonld"
        size = fetcher.size(key)
        if size is None:
            rep.assets_skipped_reason = "no assets.jsonld"
        elif max_assets_mb and size > max_assets_mb * 2**20:
            rep.assets_skipped_reason = f"assets.jsonld is {size / 2**20:.0f} MB"
        else:
            try:
                assets = fetcher.get_json(key)
            except Exception as e:
                rep.assets_skipped_reason = f"{type(e).__name__}: {e}"
            else:
                rep.assets_scanned = len(assets)
                for i, asset in enumerate(assets):
                    for f in scan(asset, targets):
                        f.path = f"{asset.get('path', i)}:{f.path}"
                        rep.asset_findings.append(f)
    return rep


def list_versions(
    fetcher: Fetcher, dandisets: List[str], include_draft: bool, jobs: int
) -> List[Tuple[str, str]]:
    if not dandisets:
        dandisets = [d for d in fetcher.list_prefixes("dandisets/") if d.isdigit()]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        listings = pool.map(
            lambda ds: (ds, fetcher.list_prefixes(f"dandisets/{ds}/")), dandisets
        )
        return sorted(
            (ds, v)
            for ds, versions in listings
            for v in versions
            if VERSION_RE.match(v) or (include_draft and v == "draft")
        )


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--bucket-url", default=DEFAULT_BUCKET_URL)
    p.add_argument(
        "--dandiset",
        action="append",
        default=[],
        help="Limit to this Dandiset id (repeatable). Default: all.",
    )
    p.add_argument("--include-draft", action="store_true")
    p.add_argument(
        "--schema-key",
        action="append",
        default=None,
        help="schemaKey to check (repeatable). Default: every class with an "
        "optional `name`, derived from the installed dandischema.",
    )
    p.add_argument("--no-validate", dest="validate", action="store_false")
    p.add_argument("--assets", action="store_true", help="Also scan assets.jsonld")
    p.add_argument(
        "--max-assets-mb",
        type=float,
        default=200,
        help="Skip assets.jsonld larger than this (0 = no limit). Default: 200",
    )
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--jobs", "-j", type=int, default=8)
    p.add_argument("--output", "-o", type=Path, help="Write per-version JSON lines")
    args = p.parse_args(argv)

    targets = set(args.schema_key) if args.schema_key else optional_name_schema_keys()
    print(f"Checking schemaKeys: {', '.join(sorted(targets))}", file=sys.stderr)

    fetcher = Fetcher(args.bucket_url, args.cache_dir)
    versions = list_versions(fetcher, args.dandiset, args.include_draft, args.jobs)
    print(f"{len(versions)} versions to audit", file=sys.stderr)

    reports: List[VersionReport] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = [
            pool.submit(
                audit_version,
                fetcher,
                ds,
                v,
                targets,
                args.validate,
                args.assets,
                args.max_assets_mb,
            )
            for ds, v in versions
        ]
        for n, fut in enumerate(as_completed(futs), 1):
            rep = fut.result()
            reports.append(rep)
            if rep.findings or rep.asset_findings or rep.fetch_error:
                print(
                    f"[{n}/{len(futs)}] {rep.dandiset}/{rep.version}: {rep.verdict}"
                    f" ({len(rep.findings)} dandiset-level,"
                    f" {len(rep.asset_findings)} asset-level findings)",
                    file=sys.stderr,
                )

    reports.sort(key=lambda r: (r.dandiset, r.version))
    if args.output:
        with args.output.open("w") as fh:
            for rep in reports:
                fh.write(json.dumps({**asdict(rep), "verdict": rep.verdict}) + "\n")

    # ---- summary -----------------------------------------------------------
    verdicts = Counter(r.verdict for r in reports)
    by_key: Counter[Tuple[str, str, bool]] = Counter()
    asset_by_key: Counter[Tuple[str, str, bool]] = Counter()
    for r in reports:
        by_key.update((f.schema_key, f.kind, f.has_identifier) for f in r.findings)
        asset_by_key.update(
            (f.schema_key, f.kind, f.has_identifier) for f in r.asset_findings
        )

    print(f"\n# Versions audited: {len(reports)}")
    for v, c in sorted(verdicts.items()):
        print(f"  {v:16} {c}")
    for title, counter in (
        ("Dandiset-level", by_key),
        ("Asset-level", asset_by_key),
    ):
        if not counter:
            continue
        print(f"\n# {title} findings (schemaKey, kind, has identifier): count")
        for (sk, kind, has_id), c in sorted(counter.items()):
            print(f"  {sk:26} {kind:8} {'id' if has_id else 'no-id':6} {c}")
    breaking = [r for r in reports if r.verdict == "WOULD_BREAK"]
    if breaking:
        print("\n# Published versions that are valid now but would become invalid:")
        for r in breaking:
            paths = ", ".join(
                f"{f.path}({f.schema_key})" for f in r.findings if f.kind == "missing"
            )
            print(f"  {r.dandiset}/{r.version}: {paths}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
