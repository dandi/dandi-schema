# Remove all `notes` entries matching any of the configured regex patterns
# from YAML content. Reads from stdin, writes to stdout.

import re
import sys

from ruamel.yaml import YAML

PATTERNS = [
    r"pydantic2linkml: Impossible to generate slot usage entry for the schemaKey",
    r"Length constraint of min_length=[a-zA-Z0-9]+, max_length=[a-zA-Z0-9]+ expressed "
    r"as a pattern entry",
]


def process(obj):
    if isinstance(obj, dict):
        if "notes" in obj:
            to_remove = [
                i
                for i, note in enumerate(obj["notes"])
                if any(re.search(p, note) for p in PATTERNS)
            ]
            for i in reversed(to_remove):
                del obj["notes"][i]
            if not obj["notes"]:
                del obj["notes"]
        for value in obj.values():
            process(value)
    elif isinstance(obj, list):
        for item in obj:
            process(item)


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
