"""Advisory (non-fatal) checks of DANDI metadata

Unlike `dandischema.metadata.validate`, which raises on any violation of the
schema, `lint` never raises on data problems and never affects validity.  It
returns a list of `LintIssue` for metadata which is valid but likely
unintended, e.g. nested records carrying nothing but their ``schemaKey``.
Consumers decide how to surface them: ``dandi validate`` (dandi-cli) can map
them onto its own ``Severity`` levels (the numeric values of `LintSeverity`
match them), and the archive can show them alongside validation errors
without blocking publication.

Checks here are deliberately kept out of the models: they are not part of the
schema, so they need no representation in JSON Schema or LinkML.
"""

from __future__ import annotations

from enum import IntEnum
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Tuple, Union

from pydantic import BaseModel

from . import models

Loc = Tuple[Union[str, int], ...]


class LintSeverity(IntEnum):
    """Severity of a `LintIssue`

    Values match those of ``dandi.validate.Severity`` in dandi-cli.
    """

    HINT = 20
    """Metadata is valid but could be improved"""

    WARNING = 30
    """Metadata is valid but should be changed; may become invalid in the future"""


class LintIssue(BaseModel):
    """A single advisory finding produced by `lint`"""

    id: str
    """Identifier of the check, e.g. ``"dandischema.empty_record"``"""

    severity: LintSeverity

    loc: Loc
    """Location of the offending record within the linted instance"""

    schema_key: str
    """``schemaKey`` of the offending record"""

    message: str


_NO_DEFAULT = object()


@lru_cache(maxsize=None)
def _field_defaults(schema_key: str) -> Dict[str, Any]:
    """Map field names of the model named ``schema_key`` to their defaults

    Fields without a default map to ``_NO_DEFAULT``. An unknown ``schema_key``
    yields an empty mapping.
    """
    model = getattr(models, schema_key, None)
    if not (isinstance(model, type) and issubclass(model, BaseModel)):
        return {}
    return {
        name: (_NO_DEFAULT if field.is_required() else field.get_default())
        for name, field in model.model_fields.items()
    }


def _is_blank(value: Any, default: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return default is not _NO_DEFAULT and bool(value == default)


def is_empty_record(record: Dict[str, Any]) -> bool:
    """Whether a record carries no information besides its ``schemaKey``

    A field is considered to carry no information if it is ``None``, an empty
    list or dict, a blank string, or equal to the default value of the field in
    the model corresponding to the record's ``schemaKey``.

    Parameters
    ----------
    record : dict
        A metadata record with a ``schemaKey``

    Returns
    -------
    bool
    """
    defaults = _field_defaults(str(record.get("schemaKey")))
    return all(
        _is_blank(value, defaults.get(name, _NO_DEFAULT))
        for name, value in record.items()
        if name != "schemaKey"
    )


def _check_empty_record(record: Dict[str, Any], loc: Loc) -> Iterator[LintIssue]:
    if is_empty_record(record):
        schema_key = str(record["schemaKey"])
        yield LintIssue(
            id="dandischema.empty_record",
            severity=LintSeverity.WARNING,
            loc=loc,
            schema_key=schema_key,
            message=f"{schema_key} record carries no information besides its "
            "schemaKey; remove it or fill it in",
        )


_RECORD_CHECKS = (_check_empty_record,)


def _walk(obj: Any, loc: Loc) -> Iterator[LintIssue]:
    if isinstance(obj, dict):
        # The top-level instance is not checked: it is the thing being linted,
        # and its required fields are the business of `validate`.
        if loc and "schemaKey" in obj:
            for check in _RECORD_CHECKS:
                yield from check(obj, loc)
        for key, value in obj.items():
            yield from _walk(value, loc + (key,))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _walk(value, loc + (i,))


def lint(obj: Dict[str, Any]) -> List[LintIssue]:
    """Run advisory checks on a metadata instance (e.g., a Dandiset or an Asset)

    This function neither validates ``obj`` nor raises on problems in it; run
    `dandischema.metadata.validate` for that.

    Parameters
    ----------
    obj : dict
        The metadata instance, in its JSON-serializable form

    Returns
    -------
    list of LintIssue
        The issues found, in document order
    """
    return list(_walk(obj, ()))
