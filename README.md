A Python library for maintaining and managing DANDI metadata schemata. The
library helps create and validate DANDI schema-compliant metadata for Dandisets
and assets.

To use: `pip install dandischema`

Every Dandiset and associated asset has a metadata object that can be retrieved using
the DANDI API.

This library uses [Pydantic](https://github.com/samuelcolvin/pydantic) to implement
all the metadata classes. Schemas are generated on schema modifications and placed into
[this repository](https://github.com/dandi/schema/tree/master/releases).

Dandischema generates JSON schema definitions and also an associated `context.json`
file for JSON-LD compliance of the metadata models.

- models.py - contains the models and any changes should be made there
- metadata.py - contains functions for validating, migrating, and aggregating metadata
- datacite.py - converts the Dandiset metadata to a Datacite metadata structure

The generated JSON schemas can be used together with
[VJSF](https://koumoul-dev.github.io/vuetify-jsonschema-form/latest/) to create a UI
for metadata modification. The DANDI Web app uses this for Dandiset metadata modification.
