#!/usr/bin/env python3
"""Validate downloaded dandiset metadata using the LinkML validator Python API.

For every dandiset version directory produced by ``fetch_metadata.py`` this
script runs LinkML validation against ``dandischema/models.yaml`` and emits
three sibling files in the version directory:

    ``validation.json`` — machine-readable record. Wraps the structured
                          ``ValidationResult`` objects from the validator
                          (severity, message, instance index, JSON-pointer
                          path, validator name, etc.) plus a small header
                          identifying the dandiset/version/target class.

    ``validation.txt``  — human-readable transcript that is byte-equivalent
                          to what ``linkml-validate`` would have printed for
                          the same inputs (same ``[severity] [source/idx]
                          message`` template, same ``No issues found``
                          banner, same exit-code semantics). One run, two
                          outputs — we don't shell out to the CLI.

    ``SUMMARY.md``      — short markdown summary of the version's
                          validation outcome (linked from the top-level
                          report).

The target class is decided from the version's ``info.json``:

    * ``Dandiset``           — for the ``draft`` version
    * ``PublishedDandiset``  — for any non-``draft`` (i.e. published) version

Re-running is safe: by default versions that already have a
``validation.json`` are skipped. Pass ``--refresh`` to re-validate
everything.

Example
-------
::

    python validate_metadata.py linkml-validation-reports/<short-sha>/data \\
        --schema dandischema/models.yaml
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml.validator.report import Severity, ValidationResult
import typer

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


# ---------------------------------------------------------------------------
# Per-directory validation
# ---------------------------------------------------------------------------


def _validate_one(
    validator: Validator, version_dir: Path, *, refresh: bool
) -> tuple[str, int]:
    """Validate one ``<dandiset-id>/<version>`` directory.

    Reads ``info.json`` (written by ``fetch_metadata.py``) to decide the
    target class, runs the validator on ``metadata.json``, and writes
    ``validation.json`` / ``validation.txt`` / ``SUMMARY.md`` alongside
    it.

    Returns ``(target_class, n_results)`` so the caller can log a tally
    without re-reading the file.
    """
    metadata_file = version_dir / "metadata.json"
    info_file = version_dir / "info.json"
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
            return target_class, int(existing.get("problem_count", 0))
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "re-validating %s — existing validation.json is unreadable",
                version_dir,
            )

    # --- Run validation once. ---
    raw = json.loads(metadata_file.read_text())
    # ``@context`` is a JSON-LD framing field that's not part of the
    # ``Dandiset`` / ``PublishedDandiset`` LinkML class definitions, so a
    # closed-world JSON-schema check flags it as an unexpected property
    # (see linkml/linkml#3442). Strip it before validation so we don't
    # drown the report in noise that has nothing to do with the model.
    raw.pop("@context", None)
    report = validator.validate(raw, target_class=target_class)
    results: list[ValidationResult] = report.results

    # ``linkml-validate``'s exit code is 1 iff any ERROR-severity result
    # is present, else 0. We replicate that for downstream consumers
    # that key off ``exit_code``.
    has_error = any(r.severity is Severity.ERROR for r in results)
    exit_code = 1 if has_error else 0

    # --- Render the human-readable transcript (CLI-equivalent). ---
    # The CLI prints ``loader.source`` as the bracketed path; for a
    # file-backed JsonLoader that's the file path string, so use the
    # same here.
    source_label = str(metadata_file)
    if results:
        transcript_lines = [_format_cli_line(r, source_label) for r in results]
    else:
        # Mirrors the CLI's success banner so byte-equivalence holds in
        # the zero-results case too.
        transcript_lines = ["No issues found"]
    out_text.write_text("\n".join(transcript_lines) + "\n")

    # --- Persist the structured record. ---
    record = {
        "dandiset_id": info["dandiset_id"],
        "version": info["version"],
        "is_published": is_published,
        "target_class": target_class,
        "schema_version": info.get("schema_version"),
        "exit_code": exit_code,
        "problem_count": len(results),
        "problems": [_result_to_dict(r) for r in results],
    }
    out_json.write_text(json.dumps(record, indent=2) + "\n")

    # --- Per-version markdown summary, linked from the top-level report. ---
    md_lines = [
        f"# Validation summary — {info['dandiset_id']} @ {info['version']}",
        "",
        f"- **Target class:** `{target_class}`",
        f"- **Status:** {info.get('status')}",
        f"- **Modified:** {info.get('modified')}",
        f"- **schemaVersion:** {info.get('schema_version')}",
        f"- **Equivalent `linkml-validate` exit code:** {exit_code}",
        f"- **# problems:** {len(results)}",
        "",
        "## Files",
        "",
        "- [`metadata.json`](metadata.json) — raw metadata as fetched from the archive",
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
    out_md.write_text("\n".join(md_lines) + "\n")

    return target_class, len(results)


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
        help="Re-validate even when validation.json already exists.",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """Validate every ``<dandiset>/<version>/metadata.json`` under ``root``."""
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
    logger.info("found %d version directories to validate", len(version_dirs))

    for vd in version_dirs:
        try:
            target, n = _validate_one(validator, vd, refresh=refresh)
        except Exception as e:
            # Never let one broken dandiset abort the whole run.
            logger.exception("validation failed for %s: %s", vd, e)
        else:
            logger.info(
                "validated %s/%s as %s (%d problems)",
                vd.parent.name,
                vd.name,
                target,
                n,
            )


if __name__ == "__main__":
    app()
