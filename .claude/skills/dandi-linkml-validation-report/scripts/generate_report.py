#!/usr/bin/env python3
"""Generate the top-level Markdown validation report.

The report directory is expected to look like::

    linkml-validation-reports/
    ├── README.md                    <-- written by this script
    └── data/
        ├── 000003/
        │   ├── draft/
        │   │   ├── metadata.json
        │   │   ├── info.json
        │   │   ├── metadata_migrated.json
        │   │   ├── validation.json
        │   │   ├── validation.txt
        │   │   └── SUMMARY.md
        │   └── 0.230629.1955/...
        └── 000004/...

For each ``validation.json`` produced by ``validate_metadata.py``, this
script aggregates results and writes a single ``README.md`` at the top
of the report directory.

The report contains:

    * Header with the ``linkml-auto-converted`` commit hash and commit
      date (passed via ``--commit-hash`` / ``--commit-date`` so the
      script doesn't need to know which branch is in play).

    * Per-bucket summary tables, where a "bucket" is the cross product
      of *target class* (``Dandiset`` for drafts, ``PublishedDandiset``
      for published versions) and *schemaVersion* of the raw metadata.

    * For every bucket, the most common error patterns (after stripping
      the per-file path prefix added by ``linkml-validate``) so the
      reader can spot systemic issues.

    * Per-bucket index linking each version to its per-version
      ``SUMMARY.md``, so the report reads naturally on GitHub or any
      static markdown viewer — no HTTP server needed.

Example
-------
::

    python generate_report.py linkml-validation-reports \\
        --commit-hash 54085828c72b69f3b9933dbd288114a9d074ed46 \\
        --commit-date 2026-04-20T18:47:47-07:00
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import logging
from pathlib import Path

import typer

logger = logging.getLogger("generate_report")

app = typer.Typer(add_completion=False, help=__doc__.splitlines()[0])


# ---------------------------------------------------------------------------
# Loading + grouping
# ---------------------------------------------------------------------------


def _problem_pattern(problem: dict) -> str:
    """Build a grouping key for one structured problem record.

    ``validate_metadata.py`` writes each problem as a dict with at
    least ``severity`` and ``message`` (and, for JSON-schema-backed
    validation, a ``source.validator`` keyword). The path-prefixed
    text the CLI prints carries no information not already in these
    fields, so we group on ``[severity] message`` and prepend the
    failing JSON-schema validator keyword when available — that lets
    similar errors group across dandisets without regex scrubbing.
    """
    severity = problem.get("severity", "?")
    message = problem.get("message", "")
    src = problem.get("source") or {}
    validator = src.get("validator")
    prefix = f"[{severity}]"
    if validator:
        prefix += f" <{validator}>"
    return f"{prefix} {message}"


def _load_records(data_dir: Path) -> list[dict]:
    """Load every ``validation.json`` under ``data_dir``.

    Each record is augmented with the relative path to its per-version
    ``SUMMARY.md`` so the report can link directly to it.
    """
    records: list[dict] = []
    for vj in sorted(data_dir.glob("*/*/validation.json")):
        try:
            rec = json.loads(vj.read_text())
        except json.JSONDecodeError:
            logger.warning("skipping unreadable %s", vj)
            continue
        # Path to per-version SUMMARY.md, relative to README.md (which
        # sits one level above ``data_dir``).
        rec["_summary_link"] = (
            f"data/{vj.parent.parent.name}/{vj.parent.name}/SUMMARY.md"
        )
        records.append(rec)
    return records


def _bucket_key(rec: dict) -> tuple[str, str]:
    """Return the ``(class, schema_version)`` bucket key for a record.

    ``schema_version`` may legitimately be missing from very old
    metadata; we fold those into a synthetic ``"<unknown>"`` bucket so
    they're still surfaced rather than dropped.
    """
    sv = rec.get("schema_version") or "<unknown>"
    return rec["target_class"], sv


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _migration_failed(rec: dict) -> bool:
    """True if this record's metadata could not be migrated."""
    return rec.get("migration_status") == "failed"


def _render_bucket(
    fh,
    title: str,
    records: list[dict],
    *,
    top_n_patterns: int,
) -> None:
    """Render one bucket section to ``fh``.

    Emits:
      * a one-line headline counting versions / migration-failed /
        valid / failing,
      * a "top error patterns" list (validation problems only —
        migration-failed versions never reached the validator),
      * a table indexing every version with a link to its
        per-version ``SUMMARY.md``.
    """
    n_total = len(records)
    n_mig_failed = sum(1 for r in records if _migration_failed(r))
    n_validated = n_total - n_mig_failed
    # "Valid" here means migration succeeded *and* validation found no
    # problems. Migration-failed versions are excluded from both
    # ``valid`` and ``with-problems`` since validation never ran.
    n_valid = sum(
        1 for r in records if not _migration_failed(r) and r["problem_count"] == 0
    )
    n_with_problems = n_validated - n_valid

    fh.write(f"### {title}\n\n")
    headline_parts = [f"**Versions:** {n_total}"]
    if n_mig_failed:
        headline_parts.append(f"**Migration failed:** {n_mig_failed}")
    headline_parts += [
        f"**Valid:** {n_valid}",
        f"**With problems:** {n_with_problems}",
    ]
    fh.write("- " + "  •  ".join(headline_parts) + "\n\n")

    # --- Top error patterns within this bucket. ---
    pattern_counter: Counter[str] = Counter()
    for r in records:
        for problem in r.get("problems", []):
            pattern_counter[_problem_pattern(problem)] += 1
    if pattern_counter:
        fh.write(f"**Top {top_n_patterns} problem patterns:**\n\n")
        for pattern, count in pattern_counter.most_common(top_n_patterns):
            # Backticks + escape any stray backticks in the pattern itself.
            safe = pattern.replace("`", "ʼ")
            fh.write(f"- `{safe}` — {count}\n")
        fh.write("\n")

    # --- Per-version index table. ---
    fh.write("| Dandiset | Version | Problems | API Status | Modified |\n")
    fh.write("|---|---|---:|---|---|\n")
    for r in sorted(records, key=lambda x: (x["dandiset_id"], x["version"])):
        if _migration_failed(r):
            # Migration-failed versions don't have a problem count to
            # display. Render a distinct cell so the reader can spot
            # them at a glance and click through to the per-version
            # SUMMARY.md for the migration error.
            problems_cell = f"[migration failed]({r['_summary_link']})"
        elif r["problem_count"]:
            problems_cell = f"[{r['problem_count']}]({r['_summary_link']})"
        else:
            problems_cell = f"[OK]({r['_summary_link']})"
        # ``status`` and ``modified`` come from each version's ``info.json``;
        # ``_attach_info`` has already stashed them onto the record so we
        # can render the table without touching the filesystem here.
        status = r.get("_status", "?")
        modified = r.get("_modified", "?")
        fh.write(
            f"| {r['dandiset_id']} | {r['version']} | {problems_cell} "
            f"| {status} | {modified} |\n"
        )
    fh.write("\n")


def _attach_info(records: list[dict], data_dir: Path) -> None:
    """Stitch the matching ``info.json`` fields onto each record.

    We do this once after loading so ``_render_bucket`` can render the
    per-version table without re-reading the filesystem in a loop.
    """
    for r in records:
        info_path = data_dir / r["dandiset_id"] / r["version"] / "info.json"
        try:
            info = json.loads(info_path.read_text())
            r["_status"] = info.get("status")
            r["_modified"] = info.get("modified")
        except (FileNotFoundError, json.JSONDecodeError):
            pass


def _render_report(
    out_path: Path,
    records: list[dict],
    *,
    commit_hash: str,
    commit_date: str,
    branch: str,
    schema: str,
    top_n_patterns: int,
) -> None:
    """Write the top-level ``README.md`` based on ``records``."""
    # Group records into the (class, schemaVersion) buckets the report
    # is organized around.
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in records:
        buckets[_bucket_key(r)].append(r)

    with out_path.open("w") as fh:
        fh.write("# DANDI metadata — LinkML validation report\n\n")
        fh.write(f"- **Branch:** `{branch}`\n")
        fh.write(f"- **Commit:** `{commit_hash}`\n")
        fh.write(f"- **Commit date:** {commit_date}\n")
        fh.write(f"- **Schema:** `{schema}`\n")
        fh.write(f"- **Total dandiset versions checked:** {len(records)}\n\n")

        n_total = len(records)
        n_mig_failed = sum(1 for r in records if _migration_failed(r))
        n_valid = sum(
            1 for r in records if not _migration_failed(r) and r["problem_count"] == 0
        )
        n_with_problems = n_total - n_mig_failed - n_valid
        overall_parts = [f"{n_valid} valid"]
        if n_mig_failed:
            overall_parts.append(f"{n_mig_failed} migration-failed")
        overall_parts.append(f"{n_with_problems} with problems")
        fh.write(
            f"**Overall:** {' / '.join(overall_parts)} "
            f"out of {n_total} versions.\n\n"
        )

        # Draft section first (target class: Dandiset), then published.
        for cls, heading in [
            ("Dandiset", "Draft versions (target class: `Dandiset`)"),
            (
                "PublishedDandiset",
                "Published versions (target class: `PublishedDandiset`)",
            ),
        ]:
            cls_records = [r for r in records if r["target_class"] == cls]
            if not cls_records:
                continue
            fh.write(f"## {heading}\n\n")
            fh.write(f"Total: {len(cls_records)} versions.\n\n")

            # Sub-buckets: stable order — known schema versions first
            # (descending so newest tends to appear first), unknowns last.
            schema_versions = sorted(
                {sv for c, sv in buckets if c == cls and sv != "<unknown>"},
                reverse=True,
            )
            if any(sv == "<unknown>" for c, sv in buckets if c == cls):
                schema_versions.append("<unknown>")

            for sv in schema_versions:
                bucket = buckets[(cls, sv)]
                _render_bucket(
                    fh,
                    f"schemaVersion {sv}",
                    bucket,
                    top_n_patterns=top_n_patterns,
                )


# ---------------------------------------------------------------------------
# Typer entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    report_root: Path = typer.Argument(
        ...,
        help="Top-level report directory, i.e. "
        "linkml-validation-reports/. "
        "Must contain a `data/` subdirectory of validated versions.",
    ),
    commit_hash: str = typer.Option(
        ...,
        "--commit-hash",
        help="Full commit hash of the linkml-auto-converted tip "
        "(included in the report header).",
    ),
    commit_date: str = typer.Option(
        ...,
        "--commit-date",
        help="ISO-8601 commit date of the linkml-auto-converted tip.",
    ),
    branch: str = typer.Option(
        "linkml-auto-converted",
        "--branch",
        help="Branch name to print in the report header.",
    ),
    schema: str = typer.Option(
        "dandischema/models.yaml",
        "--schema",
        help="Schema path to print in the report header.",
    ),
    top_n_patterns: int = typer.Option(
        10,
        "--top-n-patterns",
        help="How many most-common problem patterns to list per bucket.",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """Aggregate per-version validation outputs into a top-level README.md."""
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        level=getattr(logging, log_level.upper()),
    )

    data_dir = report_root / "data"
    if not data_dir.is_dir():
        raise typer.BadParameter(f"no data/ directory under {report_root}")

    records = _load_records(data_dir)
    _attach_info(records, data_dir)
    logger.info("loaded %d validation records", len(records))

    out_path = report_root / "README.md"
    _render_report(
        out_path,
        records,
        commit_hash=commit_hash,
        commit_date=commit_date,
        branch=branch,
        schema=schema,
        top_n_patterns=top_n_patterns,
    )
    logger.info("wrote %s", out_path)


if __name__ == "__main__":
    app()
