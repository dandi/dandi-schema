from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, TypeVar, cast

if sys.version_info >= (3, 10, 0):
    # Available in python >= 3.10
    from importlib.resources import files
else:
    from importlib_resources import files

import jsonschema
import pydantic

from .consts import (
    ALLOWED_INPUT_SCHEMAS,
    ALLOWED_TARGET_SCHEMAS,
    ALLOWED_VALIDATION_SCHEMAS,
    DANDI_SCHEMA_VERSION,
)
from .exceptions import JsonschemaValidationError, PydanticValidationError
from . import models
from .utils import _ensure_newline, version2tuple

schema_map = {
    "Dandiset": "dandiset.json",
    "PublishedDandiset": "published-dandiset.json",
    "Asset": "asset.json",
    "PublishedAsset": "published-asset.json",
}


def generate_context():
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
    fields = {}
    for val in dir(models):
        klass = getattr(models, val)
        if not isinstance(klass, pydantic.main.ModelMetaclass):
            continue
        if hasattr(klass, "_ldmeta"):
            if "nskey" in klass._ldmeta:
                name = klass.__name__
                fields[name] = f'{klass._ldmeta["nskey"]}:{name}'
        for name, field in klass.__fields__.items():
            if name == "id":
                fields[name] = "@id"
            elif name == "schemaKey":
                fields[name] = "@type"
            elif name == "digest":
                fields[name] = "@nest"
            elif name not in fields:
                if "nskey" in field.field_info.extra:
                    fields[name] = {"@id": field.field_info.extra["nskey"] + ":" + name}
                else:
                    fields[name] = {"@id": "dandi:" + name}
                if "List" in str(field.outer_type_):
                    fields[name]["@container"] = "@set"
                if name == "contributor":
                    fields[name]["@container"] = "@list"
                if "enum" in str(field.type_) or name in ["url", "hasMember"]:
                    fields[name]["@type"] = "@id"

    for item in models.DigestType:
        fields[item.value] = {"@id": item.value, "@nest": "digest"}
    fields["Dandiset"] = "dandi:Dandiset"
    fields["Asset"] = "dandi:Asset"
    fields = {k: fields[k] for k in sorted(fields)}
    field_preamble.update(**fields)
    return {"@context": field_preamble}


def publish_model_schemata(releasedir: str) -> Path:
    version = models.get_schema_version()
    vdir = Path(releasedir, version)
    vdir.mkdir(exist_ok=True, parents=True)
    for class_, filename in schema_map.items():
        (vdir / filename).write_text(
            _ensure_newline(getattr(models, class_).schema_json(indent=2))
        )
    (vdir / "context.json").write_text(
        _ensure_newline(json.dumps(generate_context(), indent=2))
    )
    return vdir


def _validate_obj_json(data, schema, missing_ok=False):
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


def _validate_dandiset_json(data: dict, schema_dir: str) -> None:
    with Path(schema_dir, "dandiset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, schema)


def _validate_asset_json(data: dict, schema_dir: str) -> None:
    with Path(schema_dir, "asset.json").open() as fp:
        schema = json.load(fp)
    _validate_obj_json(data, schema)


def _get_schema(schema_version: str, schema_name: str) -> dict:
    return json.loads(
        files("dandischema.schema")
        .joinpath(f"releases/{schema_version}/{schema_name}")
        .read_text()
    )


def validate(
    obj, schema_version=None, schema_key=None, missing_ok=False, json_validation=False
):
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
            schema = klass.schema()
        else:
            if schema_key not in schema_map:
                raise ValueError(
                    "Only dandisets and assets can be validated "
                    "using json schema for older versions"
                )
            schema_filename = schema_map[schema_key]
            schema = _get_schema(schema_version, schema_filename)
        _validate_obj_json(obj, schema, missing_ok)
    klass = getattr(models, schema_key)
    try:
        klass(**obj)
    except pydantic.ValidationError as exc:
        messages = []
        for el in exc.errors():
            if not missing_ok or el["msg"] != "field required":
                messages.append(el)
        if messages:
            raise PydanticValidationError(messages)


def migrate(
    obj: dict, to_version: str = DANDI_SCHEMA_VERSION, skip_validation=False
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
        if "schemaKey" not in obj.get("assetsSummary"):
            obj["assetsSummary"]["schemaKey"] = "AssetsSummary"
        if "schemaKey" not in obj:
            obj["schemaKey"] = "Dandiset"
        obj["schemaVersion"] = to_version
    return obj


_stats_var_type = TypeVar("_stats_var_type", int, list)
_stats_type = Dict[str, _stats_var_type]


def _get_samples(value, stats, hierarchy):
    if "sampleType" in value:
        sampletype = value["sampleType"]["name"]
        obj = value["identifier"].replace("_", "-")
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
                subject = value["identifier"].replace("_", "-")
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
    if "nwb" in assetmeta["encodingFormat"]:
        if models.nwb_standard not in stats["dataStandard"]:
            stats["dataStandard"].append(models.nwb_standard)
    # TODO: RF assumption that any .json implies BIDS
    if set(Path(assetmeta["path"]).suffixes).intersection((".json", ".nii")):
        if models.bids_standard not in stats["dataStandard"]:
            stats["dataStandard"].append(models.bids_standard)


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
    return models.AssetsSummary(**stats).json_dict()
