import json
from pathlib import Path

import jsonschema

from .consts import DANDI_SCHEMA_VERSION
from . import models


def generate_context():
    import pydantic

    fields = {
        "@version": 1.1,
        "dandi": "http://schema.dandiarchive.org/",
        "dandiasset": "http://iri.dandiarchive.org/",
        "DANDI": "http://identifiers.org/DANDI:",
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
    return {"@context": fields}


def publish_model_schemata(releasedir):
    version = models.get_schema_version()
    vdir = Path(releasedir, version)
    vdir.mkdir(exist_ok=True, parents=True)
    (vdir / "dandiset.json").write_text(models.DandisetMeta.schema_json(indent=2))
    (vdir / "asset.json").write_text(models.AssetMeta.schema_json(indent=2))
    (vdir / "published-dandiset.json").write_text(
        models.PublishedDandisetMeta.schema_json(indent=2)
    )
    (vdir / "published-asset.json").write_text(
        models.PublishedAssetMeta.schema_json(indent=2)
    )
    (vdir / "context.json").write_text(json.dumps(generate_context(), indent=2))
    return vdir


def validate_dandiset_json(data, schema_dir):
    with Path(schema_dir, "dandiset.json").open() as fp:
        schema = json.load(fp)
    jsonschema.validate(data, schema)


def validate_asset_json(data, schema_dir):
    with Path(schema_dir, "asset.json").open() as fp:
        schema = json.load(fp)
    jsonschema.validate(data, schema)


def validate(obj, schema_version=None, schema_key=None):
    schema_key = schema_key or obj.get("schemaKey")
    if schema_key is None:
        raise ValueError("Provided object has no known schemaKey")
    schema_version = schema_version or obj.get("schemaVersion") or DANDI_SCHEMA_VERSION
    klass = getattr(models, schema_key)
    klass(**obj)
