#!/usr/bin/env python3
"""Migrate then validate downloaded dandiset metadata.

For every dandiset version directory produced by ``fetch_metadata.py`` this
script:

  1. Migrates the raw metadata to the latest ``Dandiset`` /
     ``PublishedDandiset`` schema using
     ``dandischema.metadata.migrate(skip_validation=True)``. Migration
     can fail (the source metadata may be malformed in ways the migrator
     can't handle) — that's recorded on the version and validation is
     skipped for it.

  2. For successfully migrated metadata, runs LinkML validation against
     ``dandischema/models.yaml`` using the LinkML ``Validator`` Python
     API.

Each version directory ends up with these sibling files:

    ``metadata_migrated.json`` — the migrated metadata, written only
                                 when migration succeeds. Verbatim
                                 ``metadata.json`` is preserved
                                 untouched.

    ``validation.json``        — machine-readable record. Always
                                 written. Carries a ``migration_status``
                                 field (``"success"`` or ``"failed"``).
                                 On success, the structured LinkML
                                 ``ValidationResult`` objects (severity,
                                 message, JSON-pointer path, validator
                                 keyword, etc.) are stored in the
                                 ``problems`` array. On migration
                                 failure, ``problems`` is empty.

    ``validation.txt``         — human-readable transcript. On success,
                                 byte-equivalent to what ``linkml-validate``
                                 would have printed (same ``[severity]
                                 [source/idx] message`` template, same
                                 ``No issues found`` banner). On
                                 migration failure, a one-line
                                 ``Migration failed: …`` notice instead.

    ``SUMMARY.md``             — short markdown summary of the version's
                                 outcome (linked from the top-level
                                 report).

The target class is decided from the version's ``info.json``:

    * ``Dandiset``           — for the ``draft`` version
    * ``PublishedDandiset``  — for any non-``draft`` (i.e. published) version

Re-running is safe: by default versions that already have a
``validation.json`` are skipped. Pass ``--refresh`` to re-run migration
and validation for every version.

Example
-------
::

    python validate_metadata.py linkml-validation-reports/<short-sha>/data \\
        --schema dandischema/models.yaml
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml.validator.report import Severity, ValidationResult
import typer

from dandischema.metadata import migrate

logger = logging.getLogger("validate_metadata")

app = typer.Typer(add_completion=False, help=__doc__.splitlines()[0])


# ---------------------------------------------------------------------------
# Result rendering
# ---------------------------------------------------------------------------


def _result_to_dict(r: ValidationResult) -> dict:
    """Serialize one ``ValidationResult`` into a JSON-friendly dict.

    Pydantic excludes the ``source`` field from default serialization
    (it's an arbitrary plugin-defined object), but for JSON-schema-based
    validation it carries useful grouping signals — the failing
    validator keyword (e.g. ``"required"``, ``"enum"``) and the value
    that triggered the failure. We pull those out by hand so the
    downstream report can group by validator without re-parsing
    messages.
    """
    # ``instance`` echoes the full data instance back into every result,
    # which would duplicate ``metadata.json`` per-problem and bloat the
    # record without adding any information the consumer doesn't already
    # have. Drop it.
    d = r.model_dump(mode="json", exclude={"instance"})
    src = r.source
    if src is not None:
        d["source"] = {
            "validator": getattr(src, "validator", None),
            "validator_value": getattr(src, "validator_value", None),
        }
    return d


def _format_cli_line(r: ValidationResult, source_label: str) -> str:
    """Format one result the way ``linkml-validate`` prints it.

    Mirrors the f-string in ``linkml/validator/cli.py`` exactly so the
    transcript stays byte-equivalent to the CLI's stdout.
    """
    # Match the CLI's f-string interpolation exactly: no fallback. If
    # ``instance_index`` is ``None`` (e.g. a result emitted for a non-list
    # instance), the literal ``"None"`` is what the CLI would print, and
    # mirroring that keeps the transcript byte-equivalent.
    return f"[{r.severity.value}] [{source_label}/{r.instance_index}] {r.message}"


def _atomic_write_json(path: Path, data: object) -> None:
    """Write ``data`` to ``path`` as pretty JSON via temp + ``os.replace``.

    Same all-or-nothing pattern as ``fetch_metadata.py``: if anything
    goes wrong before the rename, no file ends up at ``path``.
    """
    text = json.dumps(data, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Per-directory migration + validation
# ---------------------------------------------------------------------------


def _validate_one(
    validator: Validator, version_dir: Path, *, refresh: bool
) -> tuple[str, str, int]:
    """Migrate then validate one ``<dandiset-id>/<version>`` directory.

    Reads ``info.json`` (written by ``fetch_metadata.py``) to decide the
    target class, attempts a migration of ``metadata.json``, and — when
    migration succeeds — validates the migrated metadata against the
    LinkML schema. Writes ``metadata_migrated.json`` (on success),
    ``validation.json`` / ``validation.txt`` / ``SUMMARY.md``.

    Returns ``(target_class, migration_status, n_results)`` so the
    caller can log a tally without re-reading the file.
    ``migration_status`` is ``"success"`` or ``"failed"``;
    ``n_results`` is ``0`` when migration failed.
    """
    metadata_file = version_dir / "metadata.json"
    info_file = version_dir / "info.json"
    migrated_metadata_file = version_dir / "metadata_migrated.json"
    out_text = version_dir / "validation.txt"
    out_json = version_dir / "validation.json"
    out_md = version_dir / "SUMMARY.md"

    info = json.loads(info_file.read_text())
    is_published = bool(info.get("is_published"))
    target_class = "PublishedDandiset" if is_published else "Dandiset"

    # Resume support: if we already have a JSON record for this version
    # and the caller didn't pass --refresh, leave the directory alone.
    if out_json.exists() and not refresh:
        try:
            existing = json.loads(out_json.read_text())
            problem_count = int(existing.get("problem_count", 0))
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "re-validating %s — existing validation.json is unreadable",
                version_dir,
            )
        else:
            return (
                target_class,
                existing.get("migration_status", "success"),
                problem_count,
            )

    raw = json.loads(metadata_file.read_text())
    # ``@context`` is a JSON-LD framing field that's not part of the
    # ``Dandiset`` / ``PublishedDandiset`` LinkML class definitions, so a
    # closed-world JSON-schema check flags it as an unexpected property
    # (see linkml/linkml#3442). Strip it before migration/validation so
    # we don't drown the report in noise that has nothing to do with the
    # model.
    raw.pop("@context", None)

    # --- Migration step. ---
    # ``skip_validation=True`` keeps ``migrate`` from running its own
    # internal Pydantic validation; we want to validate against the
    # *LinkML* schema afterward, and we don't want a Pydantic failure to
    # mask a successful structural migration.
    migration_status: str
    migration_error: str | None
    migrated: dict | None
    try:
        migrated = migrate(raw, skip_validation=True)
    except Exception as e:
        # Migration helpers raise ``NotImplementedError`` /
        # ``ValueError`` for known unsupported inputs, but ``migrate``
        # also rewires Pydantic-level traversals where any number of
        # other errors can surface. Catch broadly so one bad version
        # doesn't abort the run.
        migrated = None
        migration_status = "failed"
        migration_error = repr(e)
    else:
        migration_status = "success"
        migration_error = None

    # --- Branch on migration outcome. ---
    results: list[ValidationResult]
    transcript_lines: list[str]
    exit_code: int | None

    if migration_status == "success":
        assert migrated is not None

        # Persist the migrated metadata so the report can link to it
        # and the user can inspect what was actually validated.
        _atomic_write_json(migrated_metadata_file, migrated)

        report = validator.validate(migrated, target_class=target_class)
        results = report.results

        # ``linkml-validate``'s exit code is 1 iff any ERROR-severity
        # result is present, else 0. Replicate that for downstream
        # consumers that key off ``exit_code``.
        has_error = any(r.severity is Severity.ERROR for r in results)
        exit_code = 1 if has_error else 0

        # The CLI prints ``loader.source`` as the bracketed path; for a
        # file-backed JsonLoader that's the file path string. Point
        # readers at the migrated file since that's what was actually
        # validated.
        source_label = str(migrated_metadata_file)
        if results:
            transcript_lines = [_format_cli_line(r, source_label) for r in results]
        else:
            # Mirrors the CLI's success banner so byte-equivalence holds
            # in the zero-results case too.
            transcript_lines = ["No issues found"]
    else:
        # Migration failed — leave any prior ``metadata_migrated.json``
        # alone (it would belong to a previous successful run) and
        # don't try to validate.
        results = []
        exit_code = None
        transcript_lines = [f"Migration failed: {migration_error}"]

    out_text.write_text("\n".join(transcript_lines) + "\n")

    # --- Persist the structured record. ---
    record = {
        "dandiset_id": info["dandiset_id"],
        "version": info["version"],
        "is_published": is_published,
        "target_class": target_class,
        "schema_version": info.get("schema_version"),
        "migration_status": migration_status,
        "migration_error": migration_error,
        "exit_code": exit_code,
        "problem_count": len(results),
        "problems": [_result_to_dict(r) for r in results],
    }
    _atomic_write_json(out_json, record)

    # --- Per-version markdown summary, linked from the top-level report. ---
    md_lines = [
        f"# Validation summary — {info['dandiset_id']} @ {info['version']}",
        "",
        f"- **Target class:** `{target_class}`",
        f"- **API status:** {info.get('status')}",
        f"- **Modified:** {info.get('modified')}",
        f"- **Source schemaVersion:** {info.get('schema_version')}",
        f"- **Migration status:** `{migration_status}`",
    ]
    if migration_status == "success":
        md_lines += [
            f"- **Equivalent `linkml-validate` exit code:** {exit_code}",
            f"- **# problems:** {len(results)}",
            "",
            "## Files",
            "",
            "- [`metadata.json`](metadata.json) — raw metadata as fetched from the archive",
            "- [`metadata_migrated.json`](metadata_migrated.json)"
            " — metadata after migration to the latest schema",
            "- [`validation.txt`](validation.txt) — `linkml-validate`-equivalent transcript",
            "- [`validation.json`](validation.json) — structured validation record",
            "",
        ]
        if results:
            md_lines += [
                "## First 20 problems",
                "",
                "```",
                *transcript_lines[:20],
                "```",
            ]
            if len(results) > 20:
                md_lines.append(
                    f"_… {len(results) - 20} more — see "
                    "[`validation.txt`](validation.txt)._"
                )
    else:
        md_lines += [
            "",
            "## Migration failure",
            "",
            "Validation was **not** run because the metadata could not be",
            "migrated to the latest schema version.",
            "",
            "```",
            f"{migration_error}",
            "```",
            "",
            "## Files",
            "",
            "- [`metadata.json`](metadata.json) — raw metadata as fetched from the archive",
            "- [`validation.txt`](validation.txt) — migration-failure notice",
            "- [`validation.json`](validation.json) — structured record (no validation results)",
            "",
        ]
    out_md.write_text("\n".join(md_lines) + "\n")

    return target_class, migration_status, len(results)


# ---------------------------------------------------------------------------
# Typer entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    root: Path = typer.Argument(
        ...,
        help="Top-level directory produced by fetch_metadata.py "
        "(contains <dandiset-id>/<version>/metadata.json files).",
    ),
    schema: Path = typer.Option(
        ...,
        "--schema",
        help="Path to dandischema/models.yaml (the LinkML schema).",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Re-migrate and re-validate even when validation.json already exists.",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """Migrate + validate every ``<dandiset>/<version>/metadata.json`` under ``root``."""
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        level=getattr(logging, log_level.upper()),
    )

    # Build one ``Validator`` and reuse it across every version: parsing
    # the schema is the expensive part, and the plugin configuration
    # below matches the ``linkml-validate`` CLI default
    # (``JsonschemaValidationPlugin`` with ``closed=True``), so the
    # results we collect are the same ones the CLI would have emitted.
    validator = Validator(
        schema,
        validation_plugins=[JsonschemaValidationPlugin(closed=True)],
    )

    version_dirs = sorted(
        p for p in root.glob("*/*") if p.is_dir() and (p / "metadata.json").is_file()
    )
    logger.info("found %d version directories to process", len(version_dirs))

    for vd in version_dirs:
        try:
            target, mig_status, n = _validate_one(validator, vd, refresh=refresh)
        except Exception as e:
            # Never let one broken dandiset abort the whole run.
            logger.exception("processing failed for %s: %s", vd, e)
        else:
            if mig_status == "success":
                logger.info(
                    "%s/%s — migrated, validated as %s (%d problems)",
                    vd.parent.name,
                    vd.name,
                    target,
                    n,
                )
            else:
                logger.info(
                    "%s/%s — migration failed; validation skipped",
                    vd.parent.name,
                    vd.name,
                )


if __name__ == "__main__":
    app()
