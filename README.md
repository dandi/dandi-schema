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
It uses [Pydantic](https://github.com/samuelcolvin/pydantic) models to define metadata
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

## Resources

* To learn how to interact with the DANDI archive,
see the [DANDI Docs](https://docs.dandiarchive.org).
* To file a feature request or bug report, go to https://github.com/dandi/helpdesk/issues/new/choose.
* For all other issues, contact the DANDI team: help@dandiarchive.org.
