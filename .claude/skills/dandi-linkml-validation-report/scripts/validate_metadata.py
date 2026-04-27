#!/usr/bin/env python3
"""Validate downloaded dandiset metadata using the ``linkml-validate`` CLI.

This script is a thin orchestrator. It does **not** import the LinkML
validator as a Python library; instead, for every dandiset version
directory produced by ``fetch_metadata.py`` it shells out to::

    linkml-validate -s <schema> -C <target-class> <version>/metadata.json

where the target class is decided from the version's ``info.json``:

    * ``Dandiset``           — for the ``draft`` version
    * ``PublishedDandiset``  — for any non-``draft`` (i.e. published) version

For each version directory the script writes three sibling files:

    ``validation.txt``  — verbatim stdout / stderr of ``linkml-validate``,
                          i.e. the human-readable transcript you would
                          have seen if you'd run the CLI by hand.

    ``validation.json`` — small machine-readable wrapper containing the
                          exit code, the chosen target class, the number
                          of problem lines, and the parsed problem lines
                          themselves. The report generator reads this
                          file rather than re-parsing ``validation.txt``.

    ``SUMMARY.md``       — short markdown summary of the version's
                          validation outcome (linked from the top-level
                          report).

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
import re
import subprocess

import typer

logger = logging.getLogger("validate_metadata")

app = typer.Typer(add_completion=False, help=__doc__.splitlines()[0])


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------
#
# ``linkml-validate`` prints one validation problem per stdout line and
# exits non-zero if any problems were found. We classify each line as
# either a "problem line" or noise (blank lines, the "No issues found"
# banner some versions emit, etc.) and persist the problem lines into a
# JSON record so the report generator doesn't have to re-parse the text.

_NOISE_PATTERNS = [
    re.compile(r"^\s*$"),  # blank lines
    re.compile(r"^No issues found", re.IGNORECASE),  # success banner
]


def _is_problem_line(line: str) -> bool:
    """Return True if ``line`` should be counted as a validation problem."""
    return not any(p.search(line) for p in _NOISE_PATTERNS)


def _run_linkml_validate(
    schema: Path, target_class: str, metadata_file: Path
) -> subprocess.CompletedProcess[str]:
    """Invoke ``linkml-validate`` and return the completed process.

    ``check=False`` because a non-zero exit code is the *expected*
    outcome whenever the metadata fails validation — we want to record
    that, not raise.
    """
    cmd = [
        "linkml-validate",
        "-s",
        str(schema),
        "-C",
        target_class,
        str(metadata_file),
    ]
    logger.debug("running %s", " ".join(cmd))
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Per-directory validation
# ---------------------------------------------------------------------------


def _validate_one(schema: Path, version_dir: Path, *, refresh: bool) -> tuple[str, int]:
    """Validate one ``<dandiset-id>/<version>`` directory.

    Reads ``info.json`` (written by ``fetch_metadata.py``) to decide the
    target class, runs ``linkml-validate`` on ``metadata.json``, then
    writes ``validation.txt``, ``validation.json`` and ``SUMMARY.md``
    inside ``version_dir``.

    Returns ``(target_class, n_problem_lines)`` so the caller can log a
    tally without re-reading the file.
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

    proc = _run_linkml_validate(schema, target_class, metadata_file)

    # --- Persist the raw transcript exactly as the CLI would print it. ---
    transcript = proc.stdout
    if proc.stderr:
        transcript += "\n--- stderr ---\n" + proc.stderr
    if not transcript.endswith("\n"):
        transcript += "\n"
    out_text.write_text(transcript)

    # --- Parse the transcript into a small JSON record. ---
    problem_lines = [
        line.rstrip() for line in proc.stdout.splitlines() if _is_problem_line(line)
    ]
    record = {
        "dandiset_id": info["dandiset_id"],
        "version": info["version"],
        "is_published": is_published,
        "target_class": target_class,
        "schema_version": info.get("schema_version"),
        "exit_code": proc.returncode,
        "problem_count": len(problem_lines),
        "problems": problem_lines,
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
        f"- **`linkml-validate` exit code:** {proc.returncode}",
        f"- **# problem lines:** {len(problem_lines)}",
        "",
        "## Files",
        "",
        "- [`metadata.json`](metadata.json) — raw metadata as fetched from the archive",
        "- [`validation.txt`](validation.txt) — verbatim `linkml-validate` output",
        "- [`validation.json`](validation.json) — parsed validation record",
        "",
    ]
    if problem_lines:
        md_lines += [
            "## First 20 problem lines",
            "",
            "```",
            *problem_lines[:20],
            "```",
        ]
        if len(problem_lines) > 20:
            md_lines.append(
                f"_… {len(problem_lines) - 20} more — see "
                "[`validation.txt`](validation.txt)._"
            )
    out_md.write_text("\n".join(md_lines) + "\n")

    return target_class, len(problem_lines)


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

    version_dirs = sorted(
        p for p in root.glob("*/*") if p.is_dir() and (p / "metadata.json").is_file()
    )
    logger.info("found %d version directories to validate", len(version_dirs))

    for vd in version_dirs:
        try:
            target, n = _validate_one(schema, vd, refresh=refresh)
            logger.info(
                "validated %s/%s as %s (%d problem lines)",
                vd.parent.name,
                vd.name,
                target,
                n,
            )
        except Exception as e:
            # Never let one broken dandiset abort the whole run.
            logger.exception("validation failed for %s: %s", vd, e)


if __name__ == "__main__":
    app()
