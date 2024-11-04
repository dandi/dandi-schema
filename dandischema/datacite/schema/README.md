Folder contains copies of jsonschema serializations of datacite which were
initially kept within datacite repository,

   https://github.com/datacite/schema/tree/master/source/json

but then moved to the "origin" of their manufacturing -- inveniosoftware

   https://github.com/inveniosoftware/datacite/tree/master/datacite/schemas

Those serializations are not "scripted" and apparently produced manually.
Related issues/inquiries:

- https://github.com/datacite/schema/issues/149
- https://github.com/inveniosoftware/datacite/issues/101

Versions in the suffixes of the files here were produced based on
original version tag  and output of git describe so we capture "order" within
MAJOR.MINOR versions.  e.g.

    ❯ git describe --tags --match 4.3 732cc7
    4.3-72-g732cc7e
    ❯ git describe --tags --match 4.3 aa5db5
    4.3-17-gaa5db56

for those from datacite, for the last one based on commit when was last
modified (not current master).  In "inveniosoftware" there are no tags for
versions of datacite, so we base ordering of 0.1.0 first tag there:

	❯ git log datacite-v4.3.json
	commit 24fc2ba3ded44512ce8569dc11c958da4a29f70a
	Author: Thorge Petersen <petersen@rz.uni-kiel.de>
	Date:   Fri Aug 12 09:47:45 2022 +0200

		schema: change affiliation definition to match property name

	commit dc8403fd8556858e8917b960b0721884c52a588e
	Author: Tom Morrell <tmorrell@caltech.edu>
	Date:   Thu Aug 15 12:17:21 2019 -0700

		schema: Add support for DataCite 4.3 metadata schema

	❯ git describe --match v0.1.0 24fc2ba3ded44512ce8569dc11c958da4a29f70a
	v0.1.0-66-g24fc2ba

so we get

    ❯ cp /home/yoh/proj/datacite/inveniosoftware-datacite/datacite/schemas/datacite-v4.3.json inveniosoftware-4.3-66-g24fc2ba.json
    ❯ cp /home/yoh/proj/datacite/inveniosoftware-datacite/datacite/schemas/datacite-v4.5.json inveniosoftware-4.5-81-g160250d.json
