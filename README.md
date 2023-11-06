# DANDI Schema

`dandi-schema` is a Python library for maintaining and managing DANDI metadata schemata.

## Installation

`pip install dandischema`

## Description

Every `Dandiset` and associated asset has a metadata object that can be retrieved using
the DANDI API. This library helps create and validate DANDI schema-compliant metadata for `Dandisets`
and assets. It uses [Pydantic](https://github.com/samuelcolvin/pydantic) to implement
all the metadata classes. Schemas are generated on schema modifications and placed into
[this repository](https://github.com/dandi/schema/tree/master/releases).

`dandi-schema` also generates JSON schema definitions and an associated `context.json`
file for JSON-LD compliance of the metadata models.

Important files in this repository include:
- [models.py](./dandischema/models.py) - contains the models
- [metadata.py](./dandischema/metadata.py) - contains functions for validating, migrating, and aggregating metadata
- [datacite.py](./dandischema/datacite.py) - converts the `Dandiset` metadata to a Datacite metadata structure

The generated JSON schemas can be used together with
[VJSF](https://koumoul-dev.github.io/vuetify-jsonschema-form/latest/) to create a UI
for `Dandiset` metadata modification as used for Dandiset metadata modification on https://dandiarchive.org.

Also Pydantic models are used by [DANDI Client/Library](https://github.com/dandi/dandi-cli) to validate
metadata while submitting data to the archive, and later by the [DANDI Archive](https://github.com/dandi/dandi-archive) itself to ensure
that all metadata conforms the model before Dandiset is allowed to be published and gain a DOI.
Such DOI generation is done via Datacite service, and `dandi-schema` library produces Datacite metadata records
out of the Pydantic models.

## Resources

* To learn how to interact with the DANDI archive,
see [the handbook](https://www.dandiarchive.org/handbook/).
* To file a feature request or bug report, go to https://github.com/dandi/helpdesk/issues/new/choose.
* For all other issues, contact the DANDI team: help@dandiarchive.org.
