# Sort entries in `enums.LicenseType.permissible_values` alphabetically by
# key. Reads from stdin, writes to stdout.

import sys

from ruamel.yaml import YAML


def process(data_):
    match data_:
        case {
            "enums": {"LicenseType": {"permissible_values": dict(permissible_values)}}
        }:
            sorted_items = sorted(permissible_values.items())
            permissible_values.clear()
            permissible_values.update(sorted_items)
        case _:
            raise ValueError(
                "Expected `enums.LicenseType.permissible_values` to be a mapping"
            )


try:
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(sys.stdin)
    process(data)
    yaml.dump(data, sys.stdout)
    print("sort_license_type_permissible_values: done", file=sys.stderr)
except Exception as e:
    print(f"sort_license_type_permissible_values: failed — {e}", file=sys.stderr)
    sys.exit(1)
