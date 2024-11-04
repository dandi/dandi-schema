from copy import deepcopy
from enum import Enum
from functools import lru_cache
from inspect import isclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, TypeVar, Union, cast, get_args

import jsonschema
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
    sanitize_value,
    strip_top_level_optional,
    version2tuple,
)

schema_map = {
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
    for class_, filename in schema_map.items():
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


def _validate_obj_json(data: dict, schema: dict, missing_ok: bool = False) -> None:
    validator: Union[jsonschema.Draft202012Validator, jsonschema.Draft7Validator]

    if version2tuple(data["schemaVersion"]) >= version2tuple("0.6.5"):
        # schema version 0.7.0 and above is produced with Pydantic V2
        # which is compliant with JSON Schema Draft 2020-12
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
        )
    else:
        validator = jsonschema.Draft7Validator(
            schema, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER
        )

    error_list = []
    for error in sorted(validator.iter_errors(data), key=str):
        if missing_ok and "is a required property" in error.message:
            continue
        error_list.append(error)
    if error_list:
        raise JsonschemaValidationError(error_list)


def _validate_dandiset_json(data: dict, schema_dir: Union[str, Path]) -> None:
    with Path(schema_dir, "dandiset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, schema)


def _validate_asset_json(data: dict, schema_dir: Union[str, Path]) -> None:
    with Path(schema_dir, "asset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, schema)


@lru_cache
def _get_schema(schema_version: str, schema_name: str) -> Any:
    r = requests.get(
        "https://raw.githubusercontent.com/dandi/schema/"
        f"master/releases/{schema_version}/{schema_name}"
    )
    r.raise_for_status()
    return r.json()


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
    if schema_version not in ALLOWED_VALIDATION_SCHEMAS and schema_key in schema_map:
        raise ValueError(
            f"Metadata version {schema_version} is not allowed. "
            f"Allowed are: {', '.join(ALLOWED_VALIDATION_SCHEMAS)}."
        )
    if json_validation:
        if schema_version == DANDI_SCHEMA_VERSION:
            klass = getattr(models, schema_key)
            schema = klass.model_json_schema(
                schema_generator=TransitionalGenerateJsonSchema
            )
        else:
            if schema_key not in schema_map:
                raise ValueError(
                    "Only dandisets and assets can be validated "
                    "using json schema for older versions"
                )
            schema = _get_schema(schema_version, schema_map[schema_key])
        _validate_obj_json(obj, schema, missing_ok)
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
    to_version: Optional[str] = DANDI_SCHEMA_VERSION,
    skip_validation: bool = False,
) -> dict:
    """Migrate dandiset metadata object to new schema"""
    obj = deepcopy(obj)
    if len(ALLOWED_TARGET_SCHEMAS) > 1:
        raise NotImplementedError(
            "ATM code below supports migration to current version only"
        )
    if to_version not in ALLOWED_TARGET_SCHEMAS:
        raise ValueError(f"Current target schemas: {ALLOWED_TARGET_SCHEMAS}.")
    schema_version = obj.get("schemaVersion")
    if schema_version == DANDI_SCHEMA_VERSION:
        return obj
    if schema_version not in ALLOWED_INPUT_SCHEMAS:
        raise ValueError(f"Current input schemas supported: {ALLOWED_INPUT_SCHEMAS}.")
    if version2tuple(schema_version) > version2tuple(to_version):
        raise ValueError(f"Cannot migrate from {schema_version} to lower {to_version}.")
    if not (skip_validation):
        schema = _get_schema(schema_version, "dandiset.json")
        _validate_obj_json(obj, schema)
    if version2tuple(schema_version) < version2tuple("0.6.0"):
        for val in obj.get("about", []):
            if "schemaKey" not in val:
                if "identifier" in val and "UBERON" in val["identifier"]:
                    val["schemaKey"] = "Anatomy"
                else:
                    raise ValueError("Cannot auto migrate. SchemaKey missing")
        for val in obj.get("access", []):
            if "schemaKey" not in val:
                val["schemaKey"] = "AccessRequirements"
        for resource in obj.get("relatedResource", []):
            resource["schemaKey"] = "Resource"
        if "schemaKey" not in obj["assetsSummary"]:
            obj["assetsSummary"]["schemaKey"] = "AssetsSummary"
        if "schemaKey" not in obj:
            obj["schemaKey"] = "Dandiset"
        obj["schemaVersion"] = to_version
    return obj


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

    for part in Path(assetmeta["path"]).name.split(".")[0].split("_"):
        if part.startswith("sub-"):
            subject = part.replace("sub-", "")
            if subject not in stats["subjects"]:
                stats["subjects"].append(subject)
        if part.startswith("sample-"):
            sample = part.replace("sample-", "")
            if sample not in stats["tissuesample"]:
                stats["tissuesample"].append(sample)

    stats["dataStandard"] = stats.get("dataStandard", [])

    def add_if_missing(standard: dict) -> None:
        if standard not in stats["dataStandard"]:
            stats["dataStandard"].append(standard)

    if "nwb" in assetmeta["encodingFormat"]:
        add_if_missing(models.nwb_standard)
    # TODO: RF assumption that any .json implies BIDS
    if set(Path(assetmeta["path"]).suffixes).intersection((".json", ".nii")):
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
    stats["numberOfSamples"] = (
        len(stats.pop("tissuesample", [])) + len(stats.pop("slice", []))
    ) or None
    stats["numberOfCells"] = len(stats.pop("cell", [])) or None
    return models.AssetsSummary(**stats).model_dump(mode="json", exclude_none=True)
