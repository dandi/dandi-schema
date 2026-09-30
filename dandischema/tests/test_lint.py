from typing import Any, Dict

import pytest

from ..lint import LintIssue, LintSeverity, is_empty_record, lint


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "record",
    [
        {"schemaKey": "ContactPoint"},
        {"schemaKey": "ContactPoint", "email": None, "url": ""},
        {"schemaKey": "GenericType", "name": "   "},
        # all fields at their defaults or empty
        {
            "schemaKey": "Organization",
            "roleName": [],
            "contactPoint": [],
            "includeInCitation": False,
        },
        # unknown schemaKey: only blank values count as empty
        {"schemaKey": "NoSuchModel", "foo": None},
    ],
)
def test_is_empty_record(record: Dict[str, Any]) -> None:
    assert is_empty_record(record)


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "record",
    [
        {"schemaKey": "ContactPoint", "email": "nemo@dandiarchive.org"},
        {"schemaKey": "Anatomy", "identifier": "UBERON:0004727"},
        # non-default value of a field with a default
        {"schemaKey": "Organization", "includeInCitation": True},
        # Person's default for includeInCitation is True, so False is informative
        {"schemaKey": "Person", "includeInCitation": False},
        # a field unknown to the model is informative
        {"schemaKey": "ContactPoint", "extra": "value"},
        # nested non-empty record makes the parent non-empty
        {
            "schemaKey": "EthicsApproval",
            "contactPoint": {"schemaKey": "ContactPoint"},
        },
    ],
)
def test_is_not_empty_record(record: Dict[str, Any]) -> None:
    assert not is_empty_record(record)


@pytest.mark.ai_generated
def test_lint_reports_nested_empty_records() -> None:
    meta = {
        "schemaKey": "Dandiset",
        "name": "Test",
        "ethicsApproval": [
            {
                "schemaKey": "EthicsApproval",
                "identifier": "IRB-1",
                "contactPoint": {"schemaKey": "ContactPoint"},
            }
        ],
        "access": [
            {
                "schemaKey": "AccessRequirements",
                "status": "dandi:OpenAccess",
                "contactPoint": {"schemaKey": "ContactPoint", "email": "a@b.org"},
            }
        ],
        "about": [{"schemaKey": "GenericType"}],
    }
    issues = lint(meta)
    assert issues == [
        LintIssue(
            id="dandischema.empty_record",
            severity=LintSeverity.WARNING,
            loc=("ethicsApproval", 0, "contactPoint"),
            schema_key="ContactPoint",
            message=issues[0].message,
        ),
        LintIssue(
            id="dandischema.empty_record",
            severity=LintSeverity.WARNING,
            loc=("about", 0),
            schema_key="GenericType",
            message=issues[1].message,
        ),
    ]
    assert "ContactPoint" in issues[0].message


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    "meta",
    [
        # the top-level record itself is never reported
        {"schemaKey": "Dandiset"},
        {},
        {"schemaKey": "Asset", "path": "a.nwb", "wasAttributedTo": []},
    ],
)
def test_lint_clean(meta: Dict[str, Any]) -> None:
    assert lint(meta) == []


@pytest.mark.ai_generated
def test_lint_severity_values_match_dandi_cli() -> None:
    # dandi.validate.Severity in dandi-cli: HINT = 20, WARNING = 30
    assert LintSeverity.HINT.value == 20
    assert LintSeverity.WARNING.value == 30
