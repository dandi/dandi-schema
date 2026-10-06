#!/usr/bin/env python3
"""Audit DANDI manifests for records which a schema change would invalidate.

Motivation: https://github.com/dandi/dandi-schema/issues/442 made ``name``
required on ``Contributor`` (hence ``Organization``) and ``BaseType`` subclasses
(``Anatomy``, ``SpeciesType``, ...), which were ``Optional`` in schema 0.8.0 and
earlier.  This script tells which existing versions turn from valid to invalid
by such a change, and can be reused for similar tightening of other classes.

The script walks the public S3 manifests of a DANDI instance
(``dandisets/<id>/<version>/dandiset.jsonld`` and, with ``--assets``,
``assets.jsonld``) without authentication and

1. validates every record with the *installed* ``dandischema``: Dandiset
   records are migrated to the current schema version and validated as
   ``Dandiset``, asset records are validated as ``Asset``
   (``--no-validate`` to skip);
2. reports items which point at the cause, for nested objects whose
   ``schemaKey`` belongs to one of the checked classes (by default the
   ``BaseType`` and ``Contributor`` subclasses; see ``--schema-key``):

   * ``missing`` -- ``name`` absent or ``null``
   * ``empty``   -- ``name`` is ``""`` or only whitespace

   and, for nested objects of *any* class (``--no-empty-records`` to skip):

   * ``empty_record`` -- nothing but ``schemaKey``: every other field is
     absent, ``null``, an empty string/list/dict, or equal to the field's
     default (e.g. ``{"schemaKey": "ContactPoint"}``)

The verdict is decided by validation, not by these items.  Run the script
twice: once with the ``dandischema`` preceding the change (the baseline) and
once with the changed one, passing the output of the first run with
``--baseline``.  A version is then reported as

* ``BREAKS``     -- some record (the Dandiset or an asset) validates with the
  baseline but not with the installed ``dandischema``;
* ``NEW_ERRORS`` -- no record turns invalid, but some already invalid record
  gets new validation errors;
* ``UNCHANGED``  -- otherwise.

Without ``--baseline`` a version is reported as ``VALID`` or ``INVALID``.

Examples
--------
Baseline with the released ``dandischema``, then the change, comparing the two
(``--cache-dir`` avoids downloading the manifests twice)::

    pip install dandischema==0.14.0
    python tools/audit_nameless_items.py --include-draft --assets \\
        --cache-dir ~/.cache/dandi-audit -j 16 -o baseline.jsonl
    pip install -e .
    python tools/audit_nameless_items.py --include-draft --assets \\
        --cache-dir ~/.cache/dandi-audit -j 16 -o new.jsonl \\
        --baseline baseline.jsonl

Quick look at a few Dandisets::

    python tools/audit_nameless_items.py --dandiset 000003 --dandiset 000026
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
import gzip
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

# Validation errors kept per record (the full list can be long for records
# made with old schema versions)
MAX_ERRORS = 50

_NO_DEFAULT = object()


@dataclass
class Finding:
    schema_key: str
    path: str
    kind: str  # "missing" | "empty" | "empty_record"
    has_identifier: bool
    identifier: Optional[str] = None


@dataclass
class VersionReport:
    dandiset: str
    version: str
    schema_version: Optional[str] = None
    # Validation errors ("loc: type") of the Dandiset record; None if not
    # validated, [] if valid
    errors: Optional[List[str]] = None
    # Validation errors of the invalid assets, by asset path; None if not
    # validated
    asset_errors: Optional[Dict[str, List[str]]] = None
    findings: List[Finding] = field(default_factory=list)
    asset_findings: List[Finding] = field(default_factory=list)
    assets_scanned: Optional[int] = None
    assets_skipped_reason: Optional[str] = None
    fetch_error: Optional[str] = None
    # Filled in when compared with a baseline
    verdict: Optional[str] = None
    new_errors: Dict[str, List[str]] = field(default_factory=dict)


def checked_schema_keys() -> Set[str]:
    """``schemaKey`` values of the ``BaseType`` and ``Contributor`` subclasses."""
    keys: Set[str] = set()
    for obj in vars(models).values():
        if (
            isinstance(obj, type)
            and issubclass(obj, (models.BaseType, models.Contributor))
            and obj.__module__ == models.__name__
        ):
            default = obj.model_fields["schemaKey"].default
            keys.add(default if isinstance(default, str) else obj.__name__)
    return keys


def field_defaults() -> Dict[str, Dict[str, Any]]:
    """Map ``schemaKey`` to ``{field: default}`` of the corresponding model.

    Fields without a default map to ``_NO_DEFAULT``.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for obj in vars(models).values():
        if not (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj.__module__ == models.__name__
            and "schemaKey" in obj.model_fields
        ):
            continue
        key = obj.model_fields["schemaKey"].default
        if not isinstance(key, str) or obj.__name__ != key:
            continue  # aliases and bases sharing a subclass' schemaKey
        out[key] = {
            name: (_NO_DEFAULT if f.is_required() else f.get_default())
            for name, f in obj.model_fields.items()
        }
    return out


def _is_blank(value: Any, default: Any) -> bool:
    if value is None or (isinstance(value, (str, list, dict)) and not value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return default is not _NO_DEFAULT and value == default


def is_empty_record(obj: Dict[str, Any], defaults: Dict[str, Any]) -> bool:
    """Whether ``obj`` carries no information besides its ``schemaKey``."""
    return all(
        _is_blank(v, defaults.get(k, _NO_DEFAULT))
        for k, v in obj.items()
        if k != "schemaKey"
    )


def scan(
    obj: Any,
    targets: Set[str],
    defaults: Optional[Dict[str, Dict[str, Any]]] = None,
    path: str = "",
) -> Iterator[Finding]:
    """Yield findings for nested dicts with a ``schemaKey``.

    ``targets`` are the schemaKeys checked for a missing/empty ``name``;
    if ``defaults`` (see `field_defaults`) is given, nested records of any
    schemaKey are also checked for being empty (`is_empty_record`).
    """
    if isinstance(obj, dict):
        key = obj.get("schemaKey")
        if (
            path
            and defaults is not None
            and isinstance(key, str)
            and is_empty_record(obj, defaults.get(key, {}))
        ):
            yield Finding(
                schema_key=key, path=path, kind="empty_record", has_identifier=False
            )
        elif path and key in targets:
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
            yield from scan(v, targets, defaults, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from scan(v, targets, defaults, f"{path}[{i}]")


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
        """Fetch a JSON document, caching it gzip-compressed in ``cache_dir``"""
        if self.cache_dir is not None:
            plain = self.cache_dir / key
            gz = plain.with_name(plain.name + ".gz")
            if gz.exists():
                return json.loads(gzip.decompress(gz.read_bytes()))
            if plain.exists():  # cache made by earlier versions of this script
                return json.loads(plain.read_bytes())
        r = self.session.get(f"{self.bucket_url}/{key}", timeout=600)
        r.raise_for_status()
        if self.cache_dir is not None:
            gz.parent.mkdir(parents=True, exist_ok=True)
            gz.write_bytes(gzip.compress(r.content))
        return r.json()


def _errors(e: Exception) -> List[str]:
    if isinstance(e, ValidationError):
        errs = sorted(
            {f"{'.'.join(map(str, err['loc']))}: {err['type']}" for err in e.errors()}
        )
    else:  # migration failures etc.
        errs = [f"{type(e).__name__}: {e}"[:500]]
    return errs[:MAX_ERRORS]


def validate_dandiset(meta: Dict[str, Any]) -> List[str]:
    """Validation errors of a Dandiset record with the installed ``dandischema``"""
    try:
        migrated = migrate(meta, to_version=DANDI_SCHEMA_VERSION, skip_validation=True)
        models.Dandiset.model_validate(migrated)
    except Exception as e:
        return _errors(e)
    return []


def validate_asset(meta: Dict[str, Any]) -> List[str]:
    """Validation errors of an asset record with the installed ``dandischema``"""
    try:
        models.Asset.model_validate(meta)
    except Exception as e:
        return _errors(e)
    return []


def audit_version(
    fetcher: Fetcher,
    dandiset: str,
    version: str,
    targets: Set[str],
    defaults: Optional[Dict[str, Dict[str, Any]]],
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
    rep.findings = list(scan(meta, targets, defaults))
    if do_validate:
        rep.errors = validate_dandiset(meta)
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
                if do_validate:
                    rep.asset_errors = {}
                for i, asset in enumerate(assets):
                    apath = str(asset.get("path", i))
                    for f in scan(asset, targets, defaults):
                        f.path = f"{apath}:{f.path}"
                        rep.asset_findings.append(f)
                    if rep.asset_errors is not None:
                        errs = validate_asset(asset)
                        if errs:
                            rep.asset_errors[apath] = errs
    return rep


def compare(rep: VersionReport, baseline: Optional[VersionReport]) -> None:
    """Set ``rep.verdict`` and ``rep.new_errors`` relative to ``baseline``"""
    if rep.fetch_error:
        rep.verdict = "FETCH_ERROR"
        return
    if baseline is None:
        if rep.errors is None:
            rep.verdict = "NOT_VALIDATED"
        else:
            rep.verdict = "INVALID" if rep.errors or rep.asset_errors else "VALID"
        return
    breaks = False
    # (record, errors now, errors in baseline); a record not validated in the
    # baseline is not compared
    records: List[Tuple[str, List[str], Optional[List[str]]]] = []
    if rep.errors is not None and baseline.errors is not None:
        records.append(("<dandiset>", rep.errors, baseline.errors))
    if rep.asset_errors is not None and baseline.asset_errors is not None:
        for apath, errs in rep.asset_errors.items():
            records.append((apath, errs, baseline.asset_errors.get(apath, [])))
    for name, errs, base_errs in records:
        assert base_errs is not None
        new = sorted(set(errs) - set(base_errs))
        if new:
            rep.new_errors[name] = new
            breaks = breaks or not base_errs
    if breaks:
        rep.verdict = "BREAKS"
    elif rep.new_errors:
        rep.verdict = "NEW_ERRORS"
    else:
        rep.verdict = "UNCHANGED"


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


def load_baseline(path: Path) -> Dict[Tuple[str, str], VersionReport]:
    out: Dict[Tuple[str, str], VersionReport] = {}
    with path.open() as fh:
        for line in fh:
            d = json.loads(line)
            rep = VersionReport(
                dandiset=d["dandiset"],
                version=d["version"],
                errors=d.get("errors"),
                asset_errors=d.get("asset_errors"),
            )
            out[(rep.dandiset, rep.version)] = rep
    return out


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
        help="schemaKey to check for a missing/empty `name` (repeatable). "
        "Default: the BaseType and Contributor subclasses.",
    )
    p.add_argument(
        "--no-empty-records",
        dest="empty_records",
        action="store_false",
        help="Do not check nested records of any class for carrying nothing "
        "but schemaKey",
    )
    p.add_argument("--no-validate", dest="validate", action="store_false")
    p.add_argument(
        "--baseline",
        type=Path,
        help="JSON lines output of an earlier run (with the dandischema "
        "preceding the change) to compare the validation results with",
    )
    p.add_argument("--assets", action="store_true", help="Also audit assets.jsonld")
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

    targets = set(args.schema_key) if args.schema_key else checked_schema_keys()
    print(f"Checking schemaKeys: {', '.join(sorted(targets))}", file=sys.stderr)
    defaults = field_defaults() if args.empty_records else None
    baseline = load_baseline(args.baseline) if args.baseline else None

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
                defaults,
                args.validate,
                args.assets,
                args.max_assets_mb,
            )
            for ds, v in versions
        ]
        for n, fut in enumerate(as_completed(futs), 1):
            rep = fut.result()
            if baseline is not None:
                compare(rep, baseline.get((rep.dandiset, rep.version)))
            else:
                compare(rep, None)
            reports.append(rep)
            if rep.verdict in ("BREAKS", "NEW_ERRORS", "FETCH_ERROR"):
                print(
                    f"[{n}/{len(futs)}] {rep.dandiset}/{rep.version}: {rep.verdict}",
                    file=sys.stderr,
                )

    reports.sort(key=lambda r: (r.dandiset, r.version))
    if args.output:
        with args.output.open("w") as fh:
            for rep in reports:
                fh.write(json.dumps(asdict(rep)) + "\n")

    # ---- summary -----------------------------------------------------------
    verdicts = Counter(r.verdict for r in reports)
    by_key: Counter[Tuple[str, str, bool]] = Counter()
    asset_by_key: Counter[Tuple[str, str, bool]] = Counter()
    for r in reports:
        by_key.update((f.schema_key, f.kind, f.has_identifier) for f in r.findings)
        asset_by_key.update(
            (f.schema_key, f.kind, f.has_identifier) for f in r.asset_findings
        )
    skipped = [r for r in reports if r.assets_skipped_reason]

    print(f"\n# Versions audited: {len(reports)}")
    for v, c in sorted(verdicts.items(), key=lambda kv: str(kv[0])):
        print(f"  {v!s:16} {c}")
    if args.assets:
        print(f"  assets scanned: {sum(r.assets_scanned or 0 for r in reports)}")
        print(f"  assets.jsonld skipped: {len(skipped)}")
    for title, counter in (
        ("Dandiset-level", by_key),
        ("Asset-level", asset_by_key),
    ):
        if not counter:
            continue
        print(f"\n# {title} findings (schemaKey, kind, has identifier): count")
        for (sk, kind, has_id), c in sorted(counter.items()):
            print(f"  {sk:26} {kind:12} {'id' if has_id else 'no-id':6} {c}")
    changed = [r for r in reports if r.verdict in ("BREAKS", "NEW_ERRORS")]
    if changed:
        print("\n# Versions with new validation errors (record: errors):")
        for r in changed:
            print(f"  {r.dandiset}/{r.version} [{r.verdict}]")
            for name, errs in r.new_errors.items():
                print(f"    {name}: {'; '.join(errs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
