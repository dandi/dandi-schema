from typing import Any, Dict, List, Optional, Union

import pytest

from ..utils import (
    _ensure_newline,
    find_objs,
    name2title,
    sanitize_value,
    strip_top_level_optional,
    version2tuple,
)


@pytest.mark.parametrize(
    "name,title",
    [
        ("relatedResource", "Related Resource"),
        ("identifier", "Identifier"),
        ("wasGeneratedBy", "Was Generated by"),
        ("sameAs", "Same as"),
        ("includeInCitation", "Include in Citation"),
        ("anExtraField", "An Extra Field"),
        ("propertyID", "Property ID"),
        ("fieldINeed", "Field I Need"),
        ("needsADatum", "Needs a Datum"),
        ("contentUrl", "Content URL"),
        ("ContactPoint", "Contact Point"),
    ],
)
def test_name2title(name: str, title: str) -> None:
    assert name2title(name) == title


@pytest.mark.parametrize(
    "ver,error",
    [
        ("ContactPoint", True),
        ("0.1.2", False),
        ("0.12.20", False),
        ("0.1.2a", True),
        ("0.1.2-rc1", True),
    ],
)
def test_version(ver: str, error: bool) -> None:
    if error:
        with pytest.raises(ValueError):
            version2tuple(ver)
    else:
        assert len(version2tuple(ver)) == 3


def test_newline() -> None:
    obj = "\n"
    assert _ensure_newline(obj).endswith("\n")
    obj = ""
    assert _ensure_newline(obj).endswith("\n")


@pytest.mark.parametrize(
    "input_, expected_output",
    [
        (Union[str, int, None], Union[str, int, None]),
        (Optional[Union[str, int]], Optional[Union[str, int]]),
        (Union[int], Union[int]),
        (Union[None], Union[None]),
        (Union[str, int, None, None], Union[str, int, None, None]),
        (Union[None, int, str], Union[None, int, str]),
        (Union[None, int, None, str], Union[None, int, None, str]),
        (Optional[str], str),
        (Optional[Optional[str]], str),
        (Optional[List[Optional[str]]], List[Optional[str]]),
        (Union[None, int], int),
        (Union[None, int, None], int),
        (Union[None, Dict[str, int]], Dict[str, int]),
        (int, int),
        (float, float),
    ],
)
def test_strip_top_level_optional(input_: type, expected_output: type) -> None:
    assert strip_top_level_optional(input_) == expected_output


def test_sanitize_value() -> None:
    # . is not sanitized in extension but elsewhere
    assert sanitize_value("_.ext", "extension") == "-.ext"
    assert sanitize_value("_.ext", "unrelated") == "--ext"
    assert sanitize_value("_.ext") == "--ext"
    assert sanitize_value("A;B") == "A-B"
    assert sanitize_value("A\\/B") == "A--B"
    assert sanitize_value("A\"'B") == "A--B"


@pytest.mark.parametrize(
    "instance, schema_key, expected",
    [
        # Single matching object.
        pytest.param(
            {"schemaKey": "Test", "data": 123},
            "Test",
            [{"schemaKey": "Test", "data": 123}],
            id="single-match",
        ),
        # No match.
        pytest.param(
            {"schemaKey": "NotMatch", "data": 123},
            "Test",
            [],
            id="no-match",
        ),
        # Empty dictionary should return an empty list.
        pytest.param(
            {},
            "Test",
            [],
            id="empty-dict",
        ),
        # Empty list should return an empty list.
        pytest.param(
            [],
            "Test",
            [],
            id="empty-list",
        ),
        # Nested dictionary: the matching object is nested within another dictionary.
        pytest.param(
            {"level1": {"schemaKey": "Test", "info": "nested"}},
            "Test",
            [{"schemaKey": "Test", "info": "nested"}],
            id="nested-dict",
        ),
        # List of dictionaries: only those with matching schema key are returned.
        pytest.param(
            [
                {"schemaKey": "Test", "data": 1},
                {"schemaKey": "Test", "data": 2},
                {"schemaKey": "NotTest", "data": 3},
            ],
            "Test",
            [
                {"schemaKey": "Test", "data": 1},
                {"schemaKey": "Test", "data": 2},
            ],
            id="list-of-dicts",
        ),
        # Mixed structure: nested dictionaries and lists.
        pytest.param(
            {
                "a": {"schemaKey": "Test", "value": 1},
                "b": [
                    {"schemaKey": "NotTest", "value": 2},
                    {"schemaKey": "Test", "value": 3},
                ],
                "c": "irrelevant",
                "d": [{"e": {"schemaKey": "Test", "value": 4}}],
            },
            "Test",
            [
                {"schemaKey": "Test", "value": 1},
                {"schemaKey": "Test", "value": 3},
                {"schemaKey": "Test", "value": 4},
            ],
            id="mixed-structure",
        ),
        # Non-collection type: integer.
        pytest.param(
            42,
            "Test",
            [],
            id="non-collection-int",
        ),
        # Non-collection type: string.
        pytest.param(
            "some string",
            "Test",
            [],
            id="non-collection-string",
        ),
        # Non-collection type: float.
        pytest.param(
            3.14,
            "Test",
            [],
            id="non-collection-float",
        ),
        # Non-collection type: None.
        pytest.param(
            None,
            "Test",
            [],
            id="non-collection-None",
        ),
        # Nested child: an object with the schema key contains a nested child that also
        # has the schema key.
        pytest.param(
            {"schemaKey": "Test", "child": {"schemaKey": "Test", "data": "child"}},
            "Test",
            [
                {"schemaKey": "Test", "child": {"schemaKey": "Test", "data": "child"}},
                {"schemaKey": "Test", "data": "child"},
            ],
            id="nested-child",
        ),
        # List in field:
        # The object with the given schema key has a field whose value is a list
        # containing objects, some of which also have the given schema key.
        pytest.param(
            {
                "schemaKey": "Test",
                "items": [
                    {"schemaKey": "Test", "data": "item1"},
                    {"schemaKey": "Other", "data": "item2"},
                    {"schemaKey": "Test", "data": "item3"},
                ],
            },
            "Test",
            [
                # The outer object is returned first...
                {
                    "schemaKey": "Test",
                    "items": [
                        {"schemaKey": "Test", "data": "item1"},
                        {"schemaKey": "Other", "data": "item2"},
                        {"schemaKey": "Test", "data": "item3"},
                    ],
                },
                # ...followed by the matching objects within the list.
                {"schemaKey": "Test", "data": "item1"},
                {"schemaKey": "Test", "data": "item3"},
            ],
            id="list-in-field",
        ),
    ],
)
def test_find_objs_parametrized(
    instance: Any, schema_key: str, expected: list[dict]
) -> None:
    result = find_objs(instance, schema_key)
    assert result == expected
