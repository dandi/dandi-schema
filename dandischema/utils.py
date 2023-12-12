from __future__ import annotations

import re
from typing import Iterator, List

from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema

TITLE_CASE_LOWER = {
    "a",
    "an",
    "and",
    "as",
    "but",
    "by",
    "for",
    "in",
    "nor",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def name2title(name: str) -> str:
    # For use in autopopulating the titles of model schema fields
    words: List[str] = []
    for w in split_camel_case(name):
        w = w.lower()
        if w == "id" or w == "url":
            w = w.upper()
        elif not words or w not in TITLE_CASE_LOWER:
            w = w.capitalize()
        words.append(w)
    return " ".join(words)


def split_camel_case(s: str) -> Iterator[str]:
    last_start = 0
    # Don't split apart "ID":
    for m in re.finditer(r"(?<=I)[A-CE-Z]|(?<=[^I])[A-Z]", s):
        yield s[last_start : m.start()]
        last_start = m.start()
    if last_start < len(s):
        yield s[last_start:]


def version2tuple(ver: str) -> tuple[int, int, int]:
    """Convert version to numeric tuple"""
    if m := re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", ver, flags=re.ASCII):
        return (int(m[1]), int(m[2]), int(m[3]))
    else:
        raise ValueError(r"Version must be well formed: \d+\.\d+\.\d+")


def _ensure_newline(obj: str) -> str:
    if not obj.endswith("\n"):
        return obj + "\n"
    return obj


class TransitionalGenerateJsonSchema(GenerateJsonSchema):
    """
    A transitional `GenerateJsonSchema` subclass that overrides the default behavior
    of the JSON schema generation in Pydantic V2 so that some aspects of the JSON
    schema generation process are the same as the behavior in Pydantic V1.
    """

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        # Override the default behavior for handling a schema that allows null values
        # With this override, `Optional` fields will not be indicated
        # as accepting null values in the JSON schema. This behavior is the one
        # exhibited in Pydantic V1.

        null_schema = {"type": "null"}
        inner_json_schema = self.generate_inner(schema["schema"])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            return inner_json_schema
