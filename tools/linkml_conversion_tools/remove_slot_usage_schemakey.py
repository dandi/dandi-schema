# Remove all `schemaKey` entries inside `slot_usage` blocks of class definitions
# from YAML content. Reads from stdin, writes to stdout.

import sys

from ruamel.yaml import YAML


def process(data_):
    for class_def in data_.get("classes", {}).values():
        if not isinstance(class_def, dict):
            raise ValueError(
                f"Expected class definition to be a dict, got {type(class_def)}"
            )
        if "slot_usage" in class_def:
            slot_usage = class_def["slot_usage"]
            if not isinstance(slot_usage, dict):
                raise ValueError(
                    f"Expected slot_usage to be a dict, got {type(class_def['slot_usage'])}"
                )
            if "schemaKey" in slot_usage:
                del slot_usage["schemaKey"]

            # If slot_usage is now empty, remove it entirely
            if not slot_usage:
                del class_def["slot_usage"]


try:
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(sys.stdin)
    process(data)
    yaml.dump(data, sys.stdout)
    print("remove_slot_usage_schemakey: done", file=sys.stderr)
except Exception as e:
    print(f"remove_slot_usage_schemakey: failed — {e}", file=sys.stderr)
    sys.exit(1)
