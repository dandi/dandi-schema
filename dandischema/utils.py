from __future__ import annotations

import copy
import re
from typing import Any, Dict, Iterator, List, Union, cast, get_args, get_origin

from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.protocols import Validator as JsonschemaValidator
from jsonschema.validators import validator_for
from pydantic import ConfigDict, TypeAdapter
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

from .exceptions import JsonschemaValidationError

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


def dandi_jsonschema_validator(schema: dict[str, Any]) -> JsonschemaValidator:
    """
    Create a JSON Schema validator appropriate for validating instances against the
    JSON schema of a DANDI model

    :param schema: The JSON schema of the DANDI model to validate against
    :return: The JSON schema validator
    :raises ValueError: If the schema does not have a 'schemaVersion' property that
        specifies the schema version with a 'default' field.
    :raises jsonschema.exceptions.SchemaError: If the JSON schema is invalid
    """
    if (
        "properties" not in schema
        or "schemaVersion" not in schema["properties"]
        or "default" not in schema["properties"]["schemaVersion"]
    ):
        msg = (
            "The schema must has a 'schemaVersion' property that specifies the schema "
            "version with a 'default' field."
        )
        raise ValueError(msg)

    default_validator_cls = cast(
        type[JsonschemaValidator],
        (
            Draft202012Validator
            # `"schemaVersion"` 0.6.5 and above is produced with Pydantic V2
            # which is compliant with JSON Schema Draft 2020-12
            if (
                version2tuple(schema["properties"]["schemaVersion"]["default"])
                >= version2tuple("0.6.5")
            )
            else Draft7Validator
        ),
    )

    return jsonschema_validator(
        schema, check_format=True, default_cls=default_validator_cls
    )


def jsonschema_validator(
    schema: dict[str, Any],
    *,
    check_format: bool,
    default_cls: type[JsonschemaValidator] | None = None,
) -> JsonschemaValidator:
    """
    Create a jsonschema validator appropriate for validating instances against a given
    JSON schema

    :param schema: The JSON schema to validate against
    :param check_format: Indicates whether to check the format against format
        specifications in the schema
    :param default_cls: The default JSON schema validator class to use to create the
        validator should the appropriate validator class cannot be determined based on
        the schema (by assessing the `$schema` property). If `None`, the class
        representing the latest JSON schema draft supported by the `jsonschema` package.
    :return: The JSON schema validator
    :raises jsonschema.exceptions.SchemaError: If the JSON schema is invalid
    """
    # Retrieve appropriate validator class for validating the given schema
    validator_cls: type[JsonschemaValidator] = (
        validator_for(schema, default_cls)
        if default_cls is not None
        else validator_for(schema)
    )

    # Ensure the schema is valid
    validator_cls.check_schema(schema)

    if check_format:
        # Return a validator with format checking enabled
        return validator_cls(schema, format_checker=validator_cls.FORMAT_CHECKER)

    # Return a validator with format checking disabled
    return validator_cls(schema)


def validate_json(instance: Any, validator: JsonschemaValidator) -> None:
    """
    Validate a data instance using a jsonschema validator

    :param instance: The data instance to validate
    :param validator: The JSON schema validator to use
    :raises JsonschemaValidationError: If the metadata instance is invalid, an instance
        of this exception containing a list of `jsonschema.exceptions.ValidationError`
        instances representing all the errors detected in the validation is raised
    """
    errs = sorted(validator.iter_errors(instance), key=str)

    if errs:
        raise JsonschemaValidationError(errs)


# Pydantic type adapter for a JSON object, which is of type `dict[str, Any]`
json_object_adapter = TypeAdapter(dict[str, Any], config=ConfigDict(strict=True))


def google_dataset_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform DANDI metadata to be compatible with Google Dataset Search.

    This function takes a DANDI metadata JSON-LD document and transforms it to ensure
    it passes the Google Dataset Search validator by adding or modifying required fields.

    Required properties for Google Dataset Search:
    - @type: Dataset
    - name: The name of the dataset
    - description: A description of the dataset
    - creator: The creator(s) of the dataset (with @type and name)
    - license: The license of the dataset
    - version: The version of the dataset
    - identifier: An identifier for the dataset (preferably a DOI)
    - keywords: Keywords describing the dataset

    Parameters
    ----------
    metadata : Dict[str, Any]
        The original DANDI metadata JSON-LD document

    Returns
    -------
    Dict[str, Any]
        The transformed metadata that is compatible with Google Dataset Search
    """
    # Make a deep copy to avoid modifying the original
    result = copy.deepcopy(metadata)

    # Append schema:Dataset to schemaKey
    if "schemaKey" in result:
        # If schemaKey is a string, convert it to a list
        if isinstance(result["schemaKey"], str):
            result["schemaKey"] = [result["schemaKey"], "schema:Dataset"]
        # If schemaKey is already a list, append to it
        elif isinstance(result["schemaKey"], list):
            if "schema:Dataset" not in result["schemaKey"]:
                result["schemaKey"].append("schema:Dataset")
        # Otherwise, set it directly
        else:
            result["schemaKey"] = ["schema:Dataset"]
    else:
        # If no schemaKey exists, create one
        result["schemaKey"] = ["schema:Dataset"]
    
    # Create schema:creator field from contributor if it doesn't exist
    if "schema:creator" not in result and "contributor" in result:
        # Filter contributors with Author role
        authors = [
            contrib
            for contrib in result["contributor"]
            if contrib.get("roleName") and "dcite:Author" in contrib.get("roleName", [])
        ]

        # If no authors found, use all contributors
        creators = authors if authors else result["contributor"]

        # Format creators according to schema.org requirements
        result["schema:creator"] = []
        for person in creators:
            # Create a new creator object with updated schemaKey
            creator = {
                "schemaKey": (
                    "schema:Organization"
                    if person.get("schemaKey") == "Organization"
                    else "schema:Person"
                ),
                "name": person.get("name", ""),
            }

            # Add identifier if available (ORCID for Person, ROR for Organization)
            if person.get("identifier"):
                creator["identifier"] = person["identifier"]

            result["schema:creator"].append(creator)
    
    # Update contributor schemaKey and remove roleName
    if "contributor" in result:
        updated_contributors = []
        for contributor in result["contributor"]:
            # Make a copy of the contributor
            updated_contributor = copy.deepcopy(contributor)

            # Update schemaKey if it exists
            if "schemaKey" in updated_contributor:
                if updated_contributor["schemaKey"] == "Person":
                    updated_contributor["schemaKey"] = "schema:Person"
                elif updated_contributor["schemaKey"] == "Organization":
                    updated_contributor["schemaKey"] = "schema:Organization"

            # Remove roleName if it exists
            if "roleName" in updated_contributor:
                del updated_contributor["roleName"]

            updated_contributors.append(updated_contributor)

        result["contributor"] = updated_contributors

    # Ensure license is properly formatted for schema.org
    if "license" in result:
        # Transform DANDI license format to schema.org format
        schema_licenses = []
        for license_type in result["license"]:
            # Extract the license identifier from the SPDX format
            if isinstance(license_type, str) and license_type.startswith("spdx:"):
                license_id = license_type.replace("spdx:", "")
                schema_licenses.append(f"https://spdx.org/licenses/{license_id}")
            else:
                schema_licenses.append(license_type)

        result["license"] = schema_licenses

    # Ensure version is present
    if "schemaVersion" in result and "version" not in result:
        result["version"] = result["schemaVersion"]

    # Ensure identifier is properly formatted (preferably as a DOI URL)
    if "identifier" in result and isinstance(result["identifier"], str):
        # If it's a DOI in the format "DANDI:123456", convert to a URL
        if result["identifier"].startswith("DANDI:"):
            dandiset_id = result["identifier"].replace("DANDI:", "")
            result["identifier"] = f"https://identifiers.org/DANDI:{dandiset_id}"

    # Generate keywords based on available metadata
    keywords = []

    # Add data standard as keywords
    if "assetsSummary" in result and "dataStandard" in result["assetsSummary"]:
        for std in result["assetsSummary"]["dataStandard"]:
            if "name" in std:
                keywords.append(std["name"])

    # Add species as keywords
    if "assetsSummary" in result and "species" in result["assetsSummary"]:
        for species in result["assetsSummary"]["species"]:
            if "name" in species:
                keywords.append(species["name"])

    # Add approach as keywords
    if "assetsSummary" in result and "approach" in result["assetsSummary"]:
        for approach in result["assetsSummary"]["approach"]:
            if "name" in approach:
                keywords.append(approach["name"])

    # Transform measurement technique into a list of strings and add as keywords
    if "assetsSummary" in result and "measurementTechnique" in result["assetsSummary"]:
        # Extract technique names for keywords
        for technique in result["assetsSummary"]["measurementTechnique"]:
            if "name" in technique:
                keywords.append(technique["name"])

        # Transform the measurementTechnique to a list of strings (names only)
        technique_names = []
        for technique in result["assetsSummary"]["measurementTechnique"]:
            if "name" in technique:
                technique_names.append(technique["name"])

        # Replace the original complex objects with just the names
        if technique_names:
            result["assetsSummary"]["measurementTechnique"] = technique_names

    # Add "neuroscience" as a default keyword for DANDI
    keywords.append("neuroscience")
    keywords.append("DANDI")

    # Add keywords to result if we generated any
    if keywords:
        if "keywords" not in result or not result["keywords"]:
            result["keywords"] = keywords
        else:
            # Add new keywords to existing ones, avoiding duplicates
            existing_keywords = result["keywords"]
            for keyword in keywords:
                if keyword not in existing_keywords:
                    existing_keywords.append(keyword)
            result["keywords"] = existing_keywords

    # Add datePublished if available
    if "datePublished" in result:
        # Ensure it's in the proper format
        result["datePublished"] = result["datePublished"]
    elif "dateCreated" in result:
        # Use dateCreated as a fallback
        result["datePublished"] = result["dateCreated"]

    return result
