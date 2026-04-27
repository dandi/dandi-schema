#!/usr/bin/env python3
"""Download raw ``Dandiset`` metadata from a DANDI Archive instance.

For every dandiset on the chosen instance this script writes the raw
metadata of the draft version *and* of every published version to::

    <output-dir>/<dandiset-id>/<version-or-"draft">/metadata.json

Each version directory also gets an ``info.json`` with the few fields
the downstream validation and report scripts need:

    {
      "dandiset_id":    "000003",
      "version":        "0.230629.1955",   # or "draft"
      "is_published":   true,              # false for the draft version
      "status":         "VALID",           # archive-side status
      "modified":       "2023-06-29T...",  # ISO 8601 or null
      "schema_version": "0.6.4"            # raw["schemaVersion"], may be null
    }

Re-running is safe: versions whose ``metadata.json`` already exists are
skipped unless ``--refresh`` is passed. This makes it easy to resume
after a network blip or to top up a previously-fetched directory with
newly published versions.

Example
-------
::

    python fetch_metadata.py linkml-validation-reports/<short-sha>/data
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dandi.dandiapi import DandiAPIClient, RemoteDandiset
import typer

logger = logging.getLogger("fetch_metadata")

app = typer.Typer(add_completion=False, help=__doc__.splitlines()[0])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dump_json(data: object) -> str:
    """Serialize ``data`` as pretty-printed JSON with a trailing newline.

    ``data`` is expected to be a structure of plain JSON-compatible types
    (dicts, lists, strings, numbers, bools, ``None``). Datetime objects
    must be converted by the caller — see how ``_fetch_version`` calls
    ``.isoformat()`` before stashing values into ``info``.
    """
    return json.dumps(data, indent=2) + "\n"


def _fetch_version(
    dandiset: RemoteDandiset,
    version_id: str,
    *,
    is_published: bool,
    version_dir: Path,
    refresh: bool,
) -> None:
    """Fetch ``metadata.json`` and ``info.json`` for one version.

    All-or-nothing on the destination paths: this function performs the
    network calls first, then writes both files to temporary paths in
    ``version_dir`` and only renames them into place once both have been
    written successfully. If anything fails — a raised exception or even
    abrupt termination of the process — neither destination file ever
    appears in a partially-written state, so the resume guard at the top
    of this function can trust ``metadata.json``/``info.json`` existence
    as a signal that the version was previously fetched in full. (The
    leftover ``.tmp`` files are harmless cruft that the next successful
    fetch overwrites.)

    Parameters
    ----------
    dandiset:
        The ``RemoteDandiset`` object returned by the DANDI client.
    version_id:
        Either the published version identifier (e.g. ``"0.230629.1955"``)
        or the literal string ``"draft"``.
    is_published:
        ``False`` for the draft version, ``True`` for any published
        version. Persisted into ``info.json`` so the validator can pick
        the right target class without re-querying the archive.
    version_dir:
        Destination directory; created if it does not yet exist.
    refresh:
        If ``False`` and the destination already contains both
        ``metadata.json`` and ``info.json``, do nothing.
    """
    metadata_file = version_dir / "metadata.json"
    info_file = version_dir / "info.json"
    if metadata_file.exists() and info_file.exists() and not refresh:
        logger.debug("skip %s/%s (already downloaded)", dandiset.identifier, version_id)
        return

    # --- Network: gather everything before touching the filesystem. ---
    # ``for_version`` returns a fresh handle bound to the requested version,
    # which is what ``get_raw_metadata`` and ``get_version`` need to operate on.
    ds_at_version = dandiset.for_version(version_id)
    raw = ds_at_version.get_raw_metadata()
    version_info = ds_at_version.get_version(version_id)

    info = {
        "dandiset_id": dandiset.identifier,
        "version": version_id,
        "is_published": is_published,
        # ``status`` is a ``VersionStatus`` enum member on the client.
        "status": version_info.status.value,
        # ``modified`` is a non-optional ``datetime`` per the ``Version``
        # model, so an ``isoformat()`` is always safe.
        "modified": version_info.modified.isoformat(),
        # The raw metadata's ``schemaVersion`` field is the dimension we
        # want to group by in the top-level report, so capture it now.
        "schema_version": raw.get("schemaVersion"),
    }

    # --- Filesystem: write to .tmp paths then rename into place. ---
    # Pre-rendering the JSON before opening any file keeps any
    # serialization error from leaving stray ``.tmp`` files behind.
    metadata_text = _dump_json(raw)
    info_text = _dump_json(info)

    version_dir.mkdir(parents=True, exist_ok=True)
    metadata_tmp = metadata_file.with_suffix(metadata_file.suffix + ".tmp")
    info_tmp = info_file.with_suffix(info_file.suffix + ".tmp")
    metadata_tmp.write_text(metadata_text)
    info_tmp.write_text(info_text)
    # ``os.replace`` performs the POSIX ``rename(2)`` syscall, which the
    # kernel cannot leave half-finished: either the destination ends up
    # pointing at the new content, or it stays as it was before the call
    # (i.e. nonexistent on the first fetch). That guarantee is what
    # makes the all-or-nothing behavior above hold even under SIGKILL,
    # since simply ``write_text``-ing the final paths would leave a
    # truncated file behind if the process were killed mid-write.
    os.replace(metadata_tmp, metadata_file)
    os.replace(info_tmp, info_file)

    logger.info("fetched %s/%s", dandiset.identifier, version_id)


# ---------------------------------------------------------------------------
# Typer entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    output_dir: Path = typer.Argument(
        ...,
        help="Directory under which <dandiset-id>/<version>/metadata.json "
        "files will be written.",
    ),
    dandi_instance: str = typer.Option(
        "dandi",
        "--dandi-instance",
        "-i",
        help="DANDI server instance name as understood by `DandiAPIClient."
        "for_dandi_instance`",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Re-download versions whose metadata is already on disk.",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Process at most N dandisets (useful for smoke tests).",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """Fetch metadata for all dandisets (draft + published versions)."""
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        level=getattr(logging, log_level.upper()),
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    with DandiAPIClient.for_dandi_instance(dandi_instance) as client:
        for i, dandiset in enumerate(client.get_dandisets(draft=True, order="id")):
            if limit is not None and i >= limit:
                break
            dandiset_id = dandiset.identifier
            dandiset_dir = output_dir / dandiset_id
            logger.info("processing %s", dandiset_id)

            # The draft version always exists and is what new edits land on,
            # so fetch it first.
            try:
                _fetch_version(
                    dandiset,
                    dandiset.draft_version.identifier,
                    is_published=False,
                    version_dir=dandiset_dir / "draft",
                    refresh=refresh,
                )
            except Exception as e:
                # Never let a single dandiset blow up the whole run.
                logger.error("failed draft of %s: %s", dandiset_id, e)

            # Then walk every published version (skipping the draft, which
            # ``get_versions`` also yields).
            for v in dandiset.get_versions():
                if v.identifier == "draft":
                    continue
                try:
                    _fetch_version(
                        dandiset,
                        v.identifier,
                        is_published=True,
                        version_dir=dandiset_dir / v.identifier,
                        refresh=refresh,
                    )
                except Exception as e:
                    logger.error("failed %s/%s: %s", dandiset_id, v.identifier, e)


if __name__ == "__main__":
    app()
