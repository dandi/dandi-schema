# Remove `notes` entries matching any of the configured removal rules from YAML
# content. Each rule matches a note by regex, and may optionally restrict the
# match to specific locations in the document. Reads from stdin, writes to
# stdout.

import re
import sys
from typing import Any, NamedTuple

from ruamel.yaml import YAML

# The location of a node in the document, expressed as the sequence of mapping
# keys and sequence indices to follow from the root. For example, `("classes",
# "Dandiset", "slot_usage", "wasGeneratedBy", "notes")` locates the `notes`
# describing the `wasGeneratedBy` slot usage of the `Dandiset` class.
NodePath = tuple[str | int, ...]


class Removal(NamedTuple):
    """A rule specifying which `notes` entries to remove."""

    # A regex matched against a note with `re.search()`.
    pattern: str

    # The locations the rule is confined to, or `None` to apply it to every
    # `notes` in the document. A path ending in `"notes"` designates that one
    # node and nothing below it; any other path designates a subtree root,
    # matching every `notes` at or below it.
    paths: tuple[NodePath, ...] | None = None


REMOVALS = [
    Removal(
        r"pydantic2linkml: Impossible to generate slot usage entry for the schemaKey"
    ),
    Removal(
        r"Length constraint of min_length=[a-zA-Z0-9]+, max_length=[a-zA-Z0-9]+ expressed "
        r"as a pattern entry"
    ),
]


def is_in_scope(path: NodePath, scope: NodePath) -> bool:
    """Report whether the `notes` at `path` fall within `scope`.

    A `scope` ending in `"notes"` covers only that exact node; any other
    `scope` is a subtree root and covers every `notes` at or below it.
    """
    if scope and scope[-1] == "notes":
        return path == scope
    return path[: len(scope)] == scope


def is_removable(note: str, path: NodePath) -> bool:
    """Report whether a note located at `path` should be removed."""
    return any(
        (
            removal.paths is None
            or any(is_in_scope(path, scope) for scope in removal.paths)
        )
        and re.search(removal.pattern, note)
        for removal in REMOVALS
    )


def process(obj: Any, path: NodePath = ()) -> None:
    if isinstance(obj, dict):
        if "notes" in obj:
            notes = obj["notes"]
            notes_path = path + ("notes",)
            to_remove = [
                i for i, note in enumerate(notes) if is_removable(note, notes_path)
            ]
            for i in reversed(to_remove):
                del notes[i]
            if not notes:
                del obj["notes"]
        for key, value in obj.items():
            process(value, path + (key,))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            process(item, path + (i,))


try:
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(sys.stdin)
    process(data)
    yaml.dump(data, sys.stdout)
    print("remove_notes_by_pattern: done", file=sys.stderr)
except Exception as e:
    print(f"remove_notes_by_pattern: failed — {e}", file=sys.stderr)
    sys.exit(1)
