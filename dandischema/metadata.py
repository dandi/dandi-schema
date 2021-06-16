from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, cast

import jsonschema
import requests

from .consts import ALLOWED_INPUT_SCHEMAS, ALLOWED_TARGET_SCHEMAS, DANDI_SCHEMA_VERSION
from . import models
from .utils import _ensure_newline, version2tuple


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
            elif "nskey" in field.field_info.extra:
                if name not in fields:
                    fields[name] = {"@id": field.field_info.extra["nskey"] + ":" + name}
                    if "List" in str(field.outer_type_):
                        fields[name]["@container"] = "@set"
                    if name == "contributor":
                        fields[name]["@container"] = "@list"
                    if "enum" in str(field.type_) or name == "url":
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
    (vdir / "dandiset.json").write_text(
        _ensure_newline(models.Dandiset.schema_json(indent=2))
    )
    (vdir / "asset.json").write_text(
        _ensure_newline(models.Asset.schema_json(indent=2))
    )
    (vdir / "published-dandiset.json").write_text(
        _ensure_newline(models.PublishedDandiset.schema_json(indent=2))
    )
    (vdir / "published-asset.json").write_text(
        _ensure_newline(models.PublishedAsset.schema_json(indent=2))
    )
    (vdir / "context.json").write_text(
        _ensure_newline(json.dumps(generate_context(), indent=2))
    )
    return vdir


def _validate_dandiset_json(data: dict, schema_dir: str) -> None:
    with Path(schema_dir, "dandiset.json").open() as fp:
        schema = json.load(fp)
    jsonschema.validate(data, schema)


def _validate_asset_json(data: dict, schema_dir: str) -> None:
    with Path(schema_dir, "asset.json").open() as fp:
        schema = json.load(fp)
    jsonschema.validate(data, schema)


def validate(obj, schema_version=None, schema_key=None):
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

     Returns
     -------
     None

     Raises
     --------
     ValueError:
       if no schema_key is provided and object doesn't provide schemaKey
     ValidationError
       if obj fails validation
    """
    schema_key = schema_key or obj.get("schemaKey")
    if schema_key is None:
        raise ValueError("Provided object has no known schemaKey")
    schema_version = schema_version or obj.get("schemaVersion") or DANDI_SCHEMA_VERSION
    klass = getattr(models, schema_key)
    klass(**obj)


def migrate(
    obj: dict, to_version: str = DANDI_SCHEMA_VERSION, skip_validation=False
) -> dict:
    """Migrate dandiset metadata object to new schema"""
    obj = deepcopy(obj)
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
        schema = requests.get(
            f"https://raw.githubusercontent.com/dandi/schema/"
            f"master/releases/{schema_version}/dandiset.json"
        ).json()
        jsonschema.validate(obj, schema)
    if version2tuple(schema_version) < (0, 3, 2):
        if obj.get("schemaKey") is None:
            obj["schemaKey"] = "Dandiset"
        id = obj.get("id")
        if not id.startswith("DANDI:"):
            obj["id"] = f'DANDI:{obj["id"]}'
        for contrib in obj.get("contributor", []):
            if contrib.get("roleName"):
                contrib["roleName"] = [
                    val.replace("dandi:", "dcite:") for val in contrib["roleName"]
                ]
            for affiliation in contrib.get("affiliation", []):
                affiliation["schemaKey"] = "Affiliation"
        for contrib in obj.get("relatedResource", []):
            contrib["relation"] = contrib["relation"].replace("dandi:", "dcite:")
        if "access" not in obj:
            obj["access"] = [{"status": "dandi:OpenAccess"}]
        else:
            for access in obj.get("access", []):
                access["status"] = "dandi:OpenAccess"
        if obj.get("assetsSummary") is None:
            obj["assetsSummary"] = {"numberOfFiles": 0, "numberOfBytes": 0}
        if obj.get("manifestLocation") is None:
            obj["manifestLocation"] = []
        obj["schemaVersion"] = to_version
    return obj


def _append_values(field, assetmeta, values):
    if not assetmeta.get(field):
        return values
    for val in assetmeta.get(field):
        if field == "variableMeasured":
            val = val["value"]
        if val not in values:
            values.append(val)
    return values


def _get_samples(value, stats, hierarchy):
    if "sampleType" in value:
        sampletype = value["sampleType"]["name"]
        if value["identifier"] not in stats[sampletype]:
            stats[sampletype].append(value["identifier"])
    if "wasDerivedFrom" in value:
        for entity in value["wasDerivedFrom"]:
            if entity.get("schemaKey") == "BioSample":
                stats = _get_samples(entity, stats, hierarchy)
                break
    return stats


nwb_standard = models.StandardsType(
    name="Neurodata Without Borders (NWB)", identifier="RRID:SCR_015242"
).json_dict()
bids_standard = models.StandardsType(
    name="Brain Imaging Data Structure (BIDS)", identifier="RRID:SCR_016124"
).json_dict()


def _add_asset_to_stats(assetmeta: Dict[str, Any], stats: Dict[str, Any]) -> None:
    """Add information about asset to the `stats` dict (to populate AssetsSummary)"""
    if "schemaVersion" not in assetmeta:
        raise ValueError("Provided metadata has no schema version")
    schema_version = cast(str, assetmeta.get("schemaVersion"))
    if version2tuple(schema_version) > version2tuple(DANDI_SCHEMA_VERSION):
        raise ValueError(
            f"Metadata version {schema_version} is newer than supported {DANDI_SCHEMA_VERSION}."
        )

    stats["numberOfBytes"] = stats.get("numberOfBytes", 0)
    stats["numberOfFiles"] = stats.get("numberOfFiles", 0)
    stats["numberOfBytes"] += assetmeta["contentSize"]
    stats["numberOfFiles"] += 1

    for key in ["approach", "measurementTechnique", "variableMeasured"]:
        stats[key] = _append_values(key, assetmeta, stats.get(key) or [])

    stats["subjects"] = stats.get("subjects", [])
    stats["species"] = stats.get("species", [])
    for value in assetmeta["wasAttributedTo"]:
        if value.get("schemaKey") == "Participant":
            if "species" in value:
                if value["species"] not in stats["species"]:
                    stats["species"].append(value["species"])
            if value["identifier"] not in stats["subjects"]:
                stats["subjects"].append(value["identifier"])

    hierarchy = ["cell", "slice", "tissuesample"]
    for val in hierarchy:
        stats[val] = stats.get(val, [])
    for value in assetmeta.get("wasDerivedFrom") or []:
        if value.get("schemaKey") == "BioSample":
            stats = _get_samples(value, stats, hierarchy)
            break

    stats["dataStandard"] = stats.get("dataStandard", [])
    if "nwb" in assetmeta["encodingFormat"]:
        if nwb_standard not in stats["dataStandard"]:
            stats["dataStandard"].append(nwb_standard)
    if ".nii" in assetmeta["path"] or ".json" in assetmeta["path"]:
        if bids_standard not in stats["dataStandard"]:
            stats["dataStandard"].append(bids_standard)


def toSummary(stats: dict) -> dict:
    """Convert aggregated stats to an AssetsSummary conformant dict"""
    stats["numberOfSubjects"] = len(stats["subjects"])
    stats["numberOfSamples"] = len(stats["tissuesample"]) + len(stats["slice"])
    stats["numberOfCells"] = len(stats["cell"])
    del stats["subjects"]
    del stats["tissuesample"]
    del stats["slice"]
    del stats["cell"]

    stats = {k: v if v else None for k, v in stats.items()}
    return models.AssetsSummary(**stats).json_dict()
