#!/usr/bin/env python3
"""Generate the top-level Markdown validation report.

The report directory is expected to look like::

    linkml-validation-reports/<short-sha>/
    ├── REPORT.md                    <-- written by this script
    └── data/
        ├── 000003/
        │   ├── draft/
        │   │   ├── metadata.json
        │   │   ├── info.json
        │   │   ├── validation.json
        │   │   ├── validation.txt
        │   │   └── SUMMARY.md
        │   └── 0.230629.1955/...
        └── 000004/...

For each ``validation.json`` produced by ``validate_metadata.py``, this
script aggregates results and writes a single ``REPORT.md`` at the top
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

    python generate_report.py linkml-validation-reports/<short-sha> \\
        --commit-hash 54085828c72b69f3b9933dbd288114a9d074ed46 \\
        --commit-date 2026-04-20T18:47:47-07:00
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import logging
from pathlib import Path
import re

import typer

logger = logging.getLogger("generate_report")

app = typer.Typer(add_completion=False, help=__doc__.splitlines()[0])


# ---------------------------------------------------------------------------
# Loading + grouping
# ---------------------------------------------------------------------------


# A line emitted by ``linkml-validate`` looks like::
#
#     [ERROR] [path/to/metadata.json/0] <message> in /json/pointer
#
# The bracketed source-file segment is per-version noise that prevents
# similar errors across dandisets from grouping together. This regex
# strips it so we can count error patterns meaningfully.
_SOURCE_PREFIX_RE = re.compile(r"^(\[[A-Z]+\])\s+\[[^\]]+\]\s*")


def _normalise_problem(line: str) -> str:
    """Drop the per-file source prefix from a problem line.

    Turns ``"[ERROR] [.../000003/.../metadata.json/0] foo in /bar"`` into
    ``"[ERROR] foo in /bar"``, which groups across dandisets.
    """
    return _SOURCE_PREFIX_RE.sub(r"\1 ", line, count=1)


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
        # Path to per-version SUMMARY.md, relative to REPORT.md (which
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


def _render_bucket(
    fh,
    title: str,
    records: list[dict],
    *,
    top_n_patterns: int,
) -> None:
    """Render one bucket section to ``fh``.

    Emits:
      * a one-line headline counting versions / valid / failing,
      * a "top error patterns" list,
      * a table indexing every version with a link to its
        per-version ``SUMMARY.md``.
    """
    n_total = len(records)
    n_valid = sum(1 for r in records if r["problem_count"] == 0)
    n_failing = n_total - n_valid

    fh.write(f"### {title}\n\n")
    fh.write(
        f"- **Versions:** {n_total}  •  "
        f"**Valid:** {n_valid}  •  **With problems:** {n_failing}\n\n"
    )

    # --- Top error patterns within this bucket. ---
    pattern_counter: Counter[str] = Counter()
    for r in records:
        for problem in r.get("problems", []):
            pattern_counter[_normalise_problem(problem)] += 1
    if pattern_counter:
        fh.write(f"**Top {top_n_patterns} problem patterns:**\n\n")
        for pattern, count in pattern_counter.most_common(top_n_patterns):
            # Backticks + escape any stray backticks in the pattern itself.
            safe = pattern.replace("`", "ʼ")
            fh.write(f"- `{safe}` — {count}\n")
        fh.write("\n")

    # --- Per-version index table. ---
    fh.write("| Dandiset | Version | Problems | Status | Modified |\n")
    fh.write("|---|---|---:|---|---|\n")
    for r in sorted(records, key=lambda x: (x["dandiset_id"], x["version"])):
        problems_cell = (
            f"[{r['problem_count']}]({r['_summary_link']})"
            if r["problem_count"]
            else f"[OK]({r['_summary_link']})"
        )
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
    """Write the top-level ``REPORT.md`` based on ``records``."""
    # Group records into the (class, schemaVersion) buckets the report
    # is organised around.
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

        n_valid = sum(1 for r in records if r["problem_count"] == 0)
        fh.write(
            f"**Overall:** {n_valid} valid / "
            f"{len(records) - n_valid} with problems "
            f"out of {len(records)} versions.\n\n"
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
        "linkml-validation-reports/<short-sha>/. "
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
    """Aggregate per-version validation outputs into a top-level REPORT.md."""
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

    out_path = report_root / "REPORT.md"
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
