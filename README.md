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

`dandi-schema` generates JSON schema definitions and also an associated `context.json`
file for JSON-LD compliance of the metadata models.

Important files in this repository include:
- models.py - contains the models
- metadata.py - contains functions for validating, migrating, and aggregating metadata
- datacite.py - converts the `Dandiset` metadata to a Datacite metadata structure

The generated JSON schemas can be used together with
[VJSF](https://koumoul-dev.github.io/vuetify-jsonschema-form/latest/) to create a UI
for metadata modification. The DANDI Web app uses this to modify `Dandiset` metadata.

## Resources

* To learn how to interact with the DANDI archive,
see [the handbook](https://www.dandiarchive.org/handbook/).
* To file a feature request or bug report, go to https://github.com/dandi/helpdesk/issues/new/choose.
* For all other issues, contact the DANDI team: help@dandiarchive.org.
