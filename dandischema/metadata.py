from copy import deepcopy
from enum import Enum
from functools import cache
from inspect import isclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, TypeVar, Union, cast, get_args

from jsonschema.protocols import Validator as JsonschemaValidator
import pydantic
import requests

from .consts import (
    ALLOWED_INPUT_SCHEMAS,
    ALLOWED_TARGET_SCHEMAS,
    ALLOWED_VALIDATION_SCHEMAS,
    DANDI_SCHEMA_VERSION,
)
from .exceptions import JsonschemaValidationError, PydanticValidationError
from . import models
from .utils import (
    TransitionalGenerateJsonSchema,
    _ensure_newline,
    dandi_jsonschema_validator,
    json_object_adapter,
    sanitize_value,
    strip_top_level_optional,
    validate_json,
    version2tuple,
)

# A mapping of the schema keys of DANDI models to the names of their JSON schema files
SCHEMA_MAP = {
    "Dandiset": "dandiset.json",
    "PublishedDandiset": "published-dandiset.json",
    "Asset": "asset.json",
    "PublishedAsset": "published-asset.json",
}


def generate_context() -> dict:
    import pydantic

    field_preamble = {
        "@version": 1.1,
        "dandi": "http://schema.dandiarchive.org/",
        "dcite": "http://schema.dandiarchive.org/datacite/",
        "dandiasset": "http://dandiarchive.org/asset/",
        "DANDI": "http://dandiarchive.org/dandiset/",
        "dct": "http://purl.org/dc/terms/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfa": "http://www.w3.org/ns/rdfa#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "prov": "http://www.w3.org/ns/prov#",
        "pav": "http://purl.org/pav/",
        "nidm": "http://purl.org/nidash/nidm#",
        "uuid": "http://uuid.repronim.org/",
        "rs": "http://schema.repronim.org/",
        "RRID": "https://scicrunch.org/resolver/RRID:",
        "ORCID": "https://orcid.org/",
        "ROR": "https://ror.org/",
        "PATO": "http://purl.obolibrary.org/obo/PATO_",
        "spdx": "http://spdx.org/licenses/",
    }
    fields: Dict[str, Any] = {}
    for val in dir(models):
        klass = getattr(models, val)
        if not isclass(klass) or not issubclass(klass, pydantic.BaseModel):
            continue
        if hasattr(klass, "_ldmeta"):
            if "nskey" in klass._ldmeta.default:
                name = klass.__name__
                fields[name] = f'{klass._ldmeta.default["nskey"]}:{name}'
        for name, field in klass.model_fields.items():
            if name == "id":
                fields[name] = "@id"
            elif name == "schemaKey":
                fields[name] = "@type"
            elif name == "digest":
                fields[name] = "@nest"
            elif name not in fields:
                if (
                    isinstance(field.json_schema_extra, dict)
                    and "nskey" in field.json_schema_extra
                ):
                    fields[name] = {
                        "@id": cast(str, field.json_schema_extra["nskey"]) + ":" + name
                    }
                else:
                    fields[name] = {"@id": "dandi:" + name}

                # The annotation without the top-level optional
                stripped_annotation = strip_top_level_optional(field.annotation)

                # Using stringification to detect present of list in annotation is not
                # ideal, but it works for now. A better solution should be used in the
                # future.
                if "list" in str(stripped_annotation).lower():
                    fields[name]["@container"] = "@set"

                    # Handle the case where the type of the element of a list is
                    # an Enum type
                    type_args = get_args(stripped_annotation)
                    if (
                        len(type_args) == 1
                        and isclass(type_args[0])
                        and issubclass(type_args[0], Enum)
                    ):
                        fields[name]["@type"] = "@id"

                if name == "contributor":
                    fields[name]["@container"] = "@list"
                if (
                    isclass(stripped_annotation)
                    and issubclass(stripped_annotation, Enum)
                    or name in ["url", "hasMember"]
                ):
                    fields[name]["@type"] = "@id"

    for item in models.DigestType:
        fields[item.value] = {"@id": item.value, "@nest": "digest"}
    fields["Dandiset"] = "dandi:Dandiset"
    fields["Asset"] = "dandi:Asset"
    fields = {k: fields[k] for k in sorted(fields)}
    field_preamble.update(**fields)
    return {"@context": field_preamble}


def publish_model_schemata(releasedir: Union[str, Path]) -> Path:
    version = models.get_schema_version()
    vdir = Path(releasedir, version)
    vdir.mkdir(exist_ok=True, parents=True)
    for class_, filename in SCHEMA_MAP.items():
        (vdir / filename).write_text(
            _ensure_newline(
                json.dumps(
                    getattr(models, class_).model_json_schema(
                        schema_generator=TransitionalGenerateJsonSchema
                    ),
                    indent=2,
                )
            )
        )
    (vdir / "context.json").write_text(
        _ensure_newline(json.dumps(generate_context(), indent=2))
    )
    return vdir


def _validate_obj_json(
    instance: Any, validator: JsonschemaValidator, *, missing_ok: bool = False
) -> None:
    """
    Validate a data instance using a jsonschema validator with an option to filter out
    errors related to missing required properties

    :param instance: The data instance to validate
    :param validator: The JSON schema validator to use
    :param missing_ok: Indicates whether to filter out errors related to missing
        required properties
    :raises JsonschemaValidationError: If the metadata instance is invalid, and there
        are errors detected in the validation, optionally discounting errors
        related to missing required properties. An instance of this exception containing
        a list of `jsonschema.exceptions.ValidationError` instances representing all the
        (remaining) errors detected in the validation
    """
    try:
        validate_json(instance, validator)
    except JsonschemaValidationError as e:
        if missing_ok:
            remaining_errs = [
                err for err in e.errors if "is a required property" not in err.message
            ]
            # Raise an exception only if there are errors left after filtering
            if remaining_errs:
                raise JsonschemaValidationError(remaining_errs) from e
        else:
            raise e


def _validate_dandiset_json(data: dict, schema_dir: Union[str, Path]) -> None:
    with Path(schema_dir, "dandiset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, dandi_jsonschema_validator(schema))


def _validate_asset_json(data: dict, schema_dir: Union[str, Path]) -> None:
    with Path(schema_dir, "asset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, dandi_jsonschema_validator(schema))


@cache
def _get_jsonschema_validator(
    schema_version: str, schema_key: str
) -> JsonschemaValidator:
    """
    Get jsonschema validator for validating instances against a specific DANDI schema

    :param schema_version: The version of the specific DANDI schema
    :param schema_key: The schema key that identifies the specific DANDI schema
    :return: The jsonschema validator appropriate for validating instances against the
        specific DANDI schema
    :raises ValueError: If the provided schema version is among the allowed versions,
        `ALLOWED_VALIDATION_SCHEMAS`
    :raises ValueError: If the provided schema key is not among the keys in `SCHEMA_MAP`
    :raises requests.HTTPError: If the schema cannot be fetched from the `dandi/schema`
        repository
    :raises RuntimeError: If the fetched schema is not a valid JSON object
    """
    if schema_version not in ALLOWED_VALIDATION_SCHEMAS:
        raise ValueError(
            f"DANDI schema version {schema_version} is not allowed. "
            f"Allowed are: {', '.join(ALLOWED_VALIDATION_SCHEMAS)}."
        )
    if schema_key not in SCHEMA_MAP:
        raise ValueError(
            f"Schema key must be one of {', '.join(map(repr, SCHEMA_MAP.keys()))}"
        )

    # Fetch the schema from the `dandi/schema` repository
    schema_url = (
        f"https://raw.githubusercontent.com/dandi/schema/"
        f"master/releases/{schema_version}/{SCHEMA_MAP[schema_key]}"
    )
    r = requests.get(schema_url)
    r.raise_for_status()
    schema = r.json()

    # Validate that the retrieved schema is a valid JSON object, i.e., a dictionary
    # This step is needed because the `jsonschema` package requires the schema to be a
    # `Mapping[str, Any]` object
    try:
        json_object_adapter.validate_python(schema)
    except pydantic.ValidationError as e:
        msg = (
            f"The JSON schema at {schema_url} is not a valid JSON object. "
            f"Received: {schema}"
        )
        raise RuntimeError(msg) from e

    # Create a jsonschema validator for the schema
    return dandi_jsonschema_validator(schema)


@cache
def _get_jsonschema_validator_local(schema_key: str) -> JsonschemaValidator:
    """
    Get jsonschema validator for validating instances against a specific DANDI schema
    generated from the corresponding locally defined Pydantic model

    :param schema_key: The schema key that identifies the specific DANDI schema
    :raises ValueError: If the provided schema key is not among the keys in `SCHEMA_MAP`
    """
    if schema_key not in SCHEMA_MAP:
        raise ValueError(
            f"Schema key must be one of {', '.join(map(repr, SCHEMA_MAP.keys()))}"
        )

    # The pydantic model with the specified schema key
    m: type[pydantic.BaseModel] = getattr(models, schema_key)

    return dandi_jsonschema_validator(
        m.model_json_schema(schema_generator=TransitionalGenerateJsonSchema)
    )


def validate(
    obj: dict,
    schema_version: Optional[str] = None,
    schema_key: Optional[str] = None,
    missing_ok: bool = False,
    json_validation: bool = False,
) -> None:
    """Validate object using pydantic

    Parameters
    ----------
    schema_version: str, optional
      Version of schema to validate against.  If not specified, the schema
      version specified in `schemaVersion` attribute of object will be used,
      and if not present - our current DANDI_SCHEMA_VERSION
    schema_key: str, optional
      Name of the schema key to be used, if not specified, `schemaKey` of the
      object will be consulted
    missing_ok: bool, optional
      This flag allows checking if all fields have appropriate values but ignores
      missing fields. A `ValueError` is raised with the list of all errors.
    json_validation: bool, optional
      If set to True, `obj` is first validated against the corresponding jsonschema.

     Returns
     -------
     None

     Raises
     --------
     ValueError:
       if no schema_key is provided and object doesn't provide schemaKey or
       is missing properly formatted values
     ValidationError
       if obj fails validation
    """
    schema_key = schema_key or obj.get("schemaKey")
    if schema_key is None:
        raise ValueError("Provided object has no known schemaKey")
    schema_version = schema_version or obj.get("schemaVersion")
    if schema_version not in ALLOWED_VALIDATION_SCHEMAS and schema_key in SCHEMA_MAP:
        raise ValueError(
            f"Metadata version {schema_version} is not allowed. "
            f"Allowed are: {', '.join(ALLOWED_VALIDATION_SCHEMAS)}."
        )
    if json_validation:
        if schema_version == DANDI_SCHEMA_VERSION:
            jvalidator = _get_jsonschema_validator_local(schema_key)
        else:
            if schema_key not in SCHEMA_MAP:
                raise ValueError(
                    "Only dandisets and assets can be validated "
                    "using json schema for older versions"
                )
            jvalidator = _get_jsonschema_validator(schema_version, schema_key)
        _validate_obj_json(obj, jvalidator, missing_ok=missing_ok)
    klass = getattr(models, schema_key)
    try:
        klass(**obj)
    except pydantic.ValidationError as exc:
        messages = []
        for el in exc.errors():
            if not missing_ok or el["type"] != "missing":
                messages.append(el)
        if messages:
            raise PydanticValidationError(messages)  # type: ignore[arg-type]


def migrate(
    obj: dict,
    to_version: str = DANDI_SCHEMA_VERSION,
    skip_validation: bool = False,
) -> dict:
    """
    Migrate a Dandiset metadata instance to a newer DANDI schema version

    :param obj: The Dandiset metadata instance to migrate
    :param to_version: The target DANDI schema version to migrate to
    :param skip_validation: If True, the given instance will not be validated before
        migration. Otherwise, the instance will be validated before migration.
    :return: The Dandiset metadata instance migrated to the target DANDI schema version
    :raises ValueError: If the provided instance doesn't have a `schemaVersion` field
        that specifies a valid DANDI schema version
    :raises ValueError: If `to_version` is not a valid DANDI schema version or an
        allowed target schema
    :raises ValueError: If the target DANDI schema version is lower than the DANDI
        schema version of the provided instance
    """

    # ATM, we only support the latest schema version as a target. See definition of
    # `ALLOWED_TARGET_SCHEMAS` for details
    if len(ALLOWED_TARGET_SCHEMAS) > 1:
        msg = f"Only migration to current version, {DANDI_SCHEMA_VERSION}, is supported"
        raise NotImplementedError(msg)

    # --------------------------------------------------------------
    # Validate DANDI schema version provided in the metadata instance
    # --------------------------------------------------------------
    # DANDI schema version of the provided instance
    obj_ver = obj.get("schemaVersion")
    if obj_ver is None:
        msg = (
            "The provided Dandiset metadata instance does not have a "
            "`schemaVersion` field for specifying the DANDI schema version."
        )
        raise ValueError(msg)
    if not isinstance(obj_ver, str):
        msg = (
            "The provided Dandiset metadata instance has a non-string "
            "`schemaVersion` field for specifying the DANDI schema version."
        )
        raise ValueError(msg)
    # Check if `obj_ver` is a valid DANDI schema version
    try:
        # DANDI schema version of the provided instance in tuple form
        obj_ver_tuple = version2tuple(obj_ver)
    except ValueError as e:
        msg = (
            "The provided Dandiset metadata instance has an invalid "
            "`schemaVersion` field for specifying the DANDI schema version."
        )
        raise ValueError(msg) from e
    if obj_ver not in ALLOWED_INPUT_SCHEMAS:
        msg = (
            f"The DANDI schema version of the provided Dandiset metadata instance, "
            f"{obj_ver!r}, is not one of the supported versions for input "
            f"Dandiset metadata instances. The supported versions are "
            f"{ALLOWED_INPUT_SCHEMAS}."
        )
        raise ValueError(msg)
    # ----------------------------------------------------------------

    # --------------------------------------------------------------
    # Validate `to_version`
    # --------------------------------------------------------------
    # Check if `to_version` is a valid DANDI schema version
    try:
        # The target DANDI schema version in tuple form
        target_ver_tuple = version2tuple(to_version)
    except ValueError as e:
        msg = (
            "The provided target version, {to_version!r}, is not a valid DANDI schema "
            "version."
        )
        raise ValueError(msg) from e

    # Permit only allowed target schemas
    if to_version not in ALLOWED_TARGET_SCHEMAS:
        msg = (
            f"Target version, {to_version!r}, is not among supported target schemas: "
            f"{ALLOWED_TARGET_SCHEMAS}"
        )
        raise ValueError(msg)
    # ----------------------------------------------------------------

    # Ensure the target DANDI schema version is at least the DANDI schema version
    # of the provided instance
    if obj_ver_tuple > target_ver_tuple:
        raise ValueError(f"Cannot migrate from {obj_ver} to lower {to_version}.")

    # Optionally validate the instance against the DANDI schema it specifies
    # before migration
    if not skip_validation:
        _validate_obj_json(obj, _get_jsonschema_validator(obj_ver, "Dandiset"))

    obj_migrated = deepcopy(obj)

    if obj_ver_tuple == target_ver_tuple:
        return obj_migrated

    if obj_ver_tuple < version2tuple("0.6.0") <= target_ver_tuple:
        for val in obj_migrated.get("about", []):
            if "schemaKey" not in val:
                if "identifier" in val and "UBERON" in val["identifier"]:
                    val["schemaKey"] = "Anatomy"
                else:
                    raise ValueError("Cannot auto migrate. SchemaKey missing")
        for val in obj_migrated.get("access", []):
            if "schemaKey" not in val:
                val["schemaKey"] = "AccessRequirements"
        for resource in obj_migrated.get("relatedResource", []):
            resource["schemaKey"] = "Resource"
        if (
            "assetsSummary" in obj_migrated
            and "schemaKey" not in obj_migrated["assetsSummary"]
        ):
            obj_migrated["assetsSummary"]["schemaKey"] = "AssetsSummary"
        if "schemaKey" not in obj_migrated:
            obj_migrated["schemaKey"] = "Dandiset"
        obj_migrated["schemaVersion"] = to_version
    return obj_migrated


_stats_var_type = TypeVar("_stats_var_type", int, list)
_stats_type = Dict[str, _stats_var_type]


def _get_samples(value: dict, stats: _stats_type, hierarchy: Any) -> _stats_type:
    if "sampleType" in value:
        sampletype = value["sampleType"]["name"]
        obj = sanitize_value(value["identifier"])
        if obj not in stats[sampletype]:
            stats[sampletype].append(obj)
    if "wasDerivedFrom" in value:
        for entity in value["wasDerivedFrom"]:
            if entity.get("schemaKey") == "BioSample":
                stats = _get_samples(entity, stats, hierarchy)
                break
    return stats


def _add_asset_to_stats(assetmeta: Dict[str, Any], stats: _stats_type) -> None:
    """Add information about asset to the `stats` dict (to populate AssetsSummary)"""
    if "schemaVersion" not in assetmeta:
        raise ValueError("Provided metadata has no schema version")
    schema_version = cast(str, assetmeta.get("schemaVersion"))
    if schema_version not in ALLOWED_INPUT_SCHEMAS:
        raise ValueError(
            f"Metadata version {schema_version} is not allowed. "
            f"Allowed are: {', '.join(ALLOWED_INPUT_SCHEMAS)}."
        )

    stats["numberOfBytes"] = stats.get("numberOfBytes", 0)
    stats["numberOfFiles"] = stats.get("numberOfFiles", 0)
    stats["numberOfBytes"] += assetmeta["contentSize"]
    stats["numberOfFiles"] += 1

    for key in ["approach", "measurementTechnique", "variableMeasured"]:
        stats_values = stats.get(key) or []
        for val in assetmeta.get(key) or []:
            if key == "variableMeasured":
                val = val["value"]
            if val not in stats_values:
                stats_values.append(val)
        stats[key] = stats_values

    stats["subjects"] = stats.get("subjects", [])
    stats["species"] = stats.get("species", [])
    for value in assetmeta.get("wasAttributedTo", []):
        if value.get("schemaKey") == "Participant":
            if "species" in value:
                if value["species"] not in stats["species"]:
                    stats["species"].append(value["species"])
            if value.get("identifier", None):
                subject = sanitize_value(value["identifier"])
                if subject not in stats["subjects"]:
                    stats["subjects"].append(subject)

    hierarchy = ["cell", "slice", "tissuesample"]
    for val in hierarchy:
        stats[val] = stats.get(val, [])
    for value in assetmeta.get("wasDerivedFrom") or []:
        if value.get("schemaKey") == "BioSample":
            stats = _get_samples(value, stats, hierarchy)
            break

    # which components already found, so we do not count more than
    # once in some incorrectly named datasets
    found: Dict[str, str] = {}
    for part in Path(assetmeta["path"]).name.split(".")[0].split("_"):
        if not found.get("subject") and part.startswith("sub-"):
            found["subject"] = subject = part.split("sub-", 1)[1]
            if subject not in stats["subjects"]:
                stats["subjects"].append(subject)
        if not found.get("sample") and part.startswith("sample-"):
            found["sample"] = sample = part.replace("sample-", "")
            if sample not in stats["tissuesample"]:
                stats["tissuesample"].append(sample)

    stats["dataStandard"] = stats.get("dataStandard", [])

    def add_if_missing(standard: dict) -> None:
        if standard not in stats["dataStandard"]:
            stats["dataStandard"].append(standard)

    if "nwb" in assetmeta["encodingFormat"]:
        add_if_missing(models.nwb_standard)
    # TODO: RF assumption that any .json implies BIDS
    if Path(assetmeta["path"]).name == "dataset_description.json":
        add_if_missing(models.bids_standard)
    if Path(assetmeta["path"]).suffixes == [".ome", ".zarr"]:
        add_if_missing(models.ome_ngff_standard)


# TODO?: move/bind such helpers as .from_metadata or alike within
#        model classes themselves to centralize access to those constructors.
def aggregate_assets_summary(metadata: Iterable[Dict[str, Any]]) -> dict:
    """Given an iterable of metadata records produce AssetSummary"""
    stats: _stats_type = {}
    for meta in metadata:
        _add_asset_to_stats(meta, stats)
    stats["numberOfBytes"] = stats.get("numberOfBytes", 0)
    stats["numberOfFiles"] = stats.get("numberOfFiles", 0)
    stats["numberOfSubjects"] = len(stats.pop("subjects", [])) or None
    if stats["numberOfSubjects"]:
        # Must not happen. If does -- a bug in software
        assert stats["numberOfFiles"]
        assert stats["numberOfSubjects"] <= stats["numberOfFiles"]
    stats["numberOfSamples"] = (
        len(stats.pop("tissuesample", [])) + len(stats.pop("slice", []))
    ) or None
    stats["numberOfCells"] = len(stats.pop("cell", [])) or None
    return models.AssetsSummary(**stats).model_dump(mode="json", exclude_none=True)
