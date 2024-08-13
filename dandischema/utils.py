from __future__ import annotations

import re
from typing import Any, Iterator, List, Union, get_args, get_origin

from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

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

    def generate(
        self, schema: CoreSchema, mode: JsonSchemaMode = "validation"
    ) -> JsonSchemaValue:
        json_schema = super().generate(schema, mode)

        # Set the `$schema` key with the schema dialect
        json_schema["$schema"] = self.schema_dialect

        return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        # Override the default behavior for handling a schema that allows null values
        # With this override, `Optional` fields will not be indicated
        # as accepting null values in the JSON schema. This behavior is the one
        # exhibited in Pydantic V1.

        return self.generate_inner(schema["schema"])


def strip_top_level_optional(type_: Any) -> Any:
    """
    When given a generic type, this function returns a type that is the given type without
    the top-level `Optional`. If the given type is not an `Optional`, then the given
    type is returned.

    :param type_: The type to strip the top-level `Optional` from
    :return: The given type without the top-level `Optional`

    Note: This function considers a top-level `Optional` being a `Union` of two types,
          with one of these types being the `NoneType`.
    """
    origin = get_origin(type_)
    args = get_args(type_)
    if origin is Union and len(args) == 2 and type(None) in args:
        # `type_` is an Optional
        for arg in args:
            if arg is not type(None):
                return arg
        else:
            # The execution should never reach this point for
            # the args for a Union are always distinct
            raise ValueError("Optional type does not have a non-None type")
    else:
        # `type_` is not an Optional
        return type_


def sanitize_value(value: str, field: str = "non-extension", sub: str = "-") -> str:
    """Replace all "non-compliant" characters with -

    Of particular importance is _ which we use, as in BIDS, to separate
    _key-value entries.  It is not sanitizing to BIDS level of clarity though.
    In BIDS only alphanumerics are allowed, and here we only replace some known
    to be offending symbols with `sub`.

    When `field` is not "extension", we also replace ".".

    Based on dandi.organize._sanitize_value.

    .. versionchanged:: 0.8.3

            ``sanitize_value`` added
    """
    value = re.sub(r"[_*\\/<>:|\"'?%@;,\s]", sub, value)
    if field != "extension":
        value = value.replace(".", sub)
    return value
