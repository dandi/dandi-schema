# DANDI Schema

`dandi-schema` is a Python library for maintaining and managing DANDI metadata models and schemas.

## Installation

`pip install dandischema`

## Description

[DANDI](https://scicrunch.org/resolver/RRID:SCR_017571) — the Distributed Archives for
Neurophysiology Data Integration — is a BRAIN Initiative-supported platform
for publishing, sharing, and processing cellular neurophysiology data.
Every [Dandiset](https://docs.dandiarchive.org/user-guide-sharing/creating-dandiset/)
or associated asset is described by a structured metadata object that can be
retrieved through the DANDI API. The `dandi-schema` library provides Python data models
and helper utilities to create, validate, migrate, and manage these metadata objects.
It uses [Pydantic](https://github.com/pydantic/pydantic) models to define metadata
models, and the JSON Schema schemas corresponding to the Pydantic models are generated,
versioned, and stored in the [dandi/schema](https://github.com/dandi/schema) repository
with an associated `context.json` file for JSON-LD compliance. **Both** representations
of the metadata models — the Pydantic models and their corresponding JSON Schema schemas —
are used across the DANDI ecosystem (see the
[dedicated section in DANDI Docs](https://docs.dandiarchive.org/developer-guide/integrate-external-services/#dandi-metadata-models-integration)
for integration details). Additionally, this library provides tools for converting
Dandiset metadata to [DataCite](https://datacite.org/) metadata for DOI generation.

Important files in this repository include:
- [models.py](./dandischema/models.py) - contains the Pydantic models defining the metadata models
- [metadata.py](./dandischema/metadata.py) - contains functions for validating, migrating, and aggregating metadata
- [datacite package](./dandischema/datacite) - contains functions for converting Dandiset metadata to DataCite metadata

## Customization with Vendor Information

The DANDI metadata models defined in this library can be customized with vendor-specific information.
The parameters of the customization are defined by the fields of the `Config` class in
[dandischema/conf.py](./dandischema/conf.py). The `Config` class is a subclass of
[`pydantic_settings.BaseSettings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/),
and the values of the fields in an instance of the `Config` class can be set through environment
variables and `.env` files, as documented in
[the Pydantic Settings documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
Specifically,

- The value of a field is set from an environment variable with the same name, case-insensitively,
  as one of the aliases of the field. For example, the `instance_name` field can be set from
  the `DANDI_INSTANCE_NAME` or `DJANGO_DANDI_INSTANCE_NAME` environment variable.
- A value of a complex type (e.g., `list`, `set`, `dict`) should be expressed as a JSON-encoded string
  in an environment variable. For example, the value for the `licenses` field, which is of
  type `set`, can be set from the `DANDI_LICENSES` environment variable defined as the following:
  ```shell
  export DANDI_LICENSES='["spdx:CC0-1.0", "spdx:CC-BY-4.0"]'
  ```

## Resources

* To learn how to interact with the DANDI archive,
see the [DANDI Docs](https://docs.dandiarchive.org).
* To file a feature request or bug report, go to https://github.com/dandi/helpdesk/issues/new/choose.
* For all other issues, contact the DANDI team: help@dandiarchive.org.
