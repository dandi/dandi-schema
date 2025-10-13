# 0.11.1 (Thu May 15 2025)

#### 🐛 Bug Fix

- Increase `Description` field max character length [#296](https://github.com/dandi/dandi-schema/pull/296) ([@kabilar](https://github.com/kabilar))
- Remove escaping (\) of : in 2 identifiers regexes [#290](https://github.com/dandi/dandi-schema/pull/290) ([@yarikoptic](https://github.com/yarikoptic))
- Improve (better arguments validation, avoiding repeated creation of validator objects, etc) `_validate_obj_json()` in `metadata.py` and supporting funcs [#278](https://github.com/dandi/dandi-schema/pull/278) ([@candleindark](https://github.com/candleindark))
- Improve `migrate()` in `metadata.py` [#279](https://github.com/dandi/dandi-schema/pull/279) ([@candleindark](https://github.com/candleindark))
- Update URL for DANDI Docs [#272](https://github.com/dandi/dandi-schema/pull/272) ([@kabilar](https://github.com/kabilar))

#### 🏠 Internal

- Revert version of schema to 0.6.10 since we have not yet released it [#300](https://github.com/dandi/dandi-schema/pull/300) ([@yarikoptic](https://github.com/yarikoptic))
- Avoid multiple assignments of constant `ALLOWED_INPUT_SCHEMAS` [#280](https://github.com/dandi/dandi-schema/pull/280) ([@candleindark](https://github.com/candleindark))

#### Authors: 3

- Isaac To ([@candleindark](https://github.com/candleindark))
- Kabilar Gunalan ([@kabilar](https://github.com/kabilar))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.11.0 (Tue Jan 07 2025)

#### 🚀 Enhancement

- Upgrade to datacite v4.5 serialization from inveniosoftware [#261](https://github.com/dandi/dandi-schema/pull/261) ([@yarikoptic](https://github.com/yarikoptic))
- Add "version" to datacite record and bundle datacite json serializations [#260](https://github.com/dandi/dandi-schema/pull/260) ([@yarikoptic](https://github.com/yarikoptic))
- Drop Python 3.8 support (remove typing_extensions from depends) [#262](https://github.com/dandi/dandi-schema/pull/262) ([@yarikoptic](https://github.com/yarikoptic))

#### 🐛 Bug Fix

- Use `title` in place of `examples` [#271](https://github.com/dandi/dandi-schema/pull/271) ([@waxlamp](https://github.com/waxlamp) [@satra](https://github.com/satra) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- RF: detect BIDS based on having dataset_description.json [#263](https://github.com/dandi/dandi-schema/pull/263) ([@yarikoptic](https://github.com/yarikoptic))
- Add support for detection and addition of ome/ngff "standard" into assets summary [#252](https://github.com/dandi/dandi-schema/pull/252) ([@yarikoptic](https://github.com/yarikoptic))

#### 🏠 Internal

- [gh-actions](deps): Bump codecov/codecov-action from 4 to 5 [#267](https://github.com/dandi/dandi-schema/pull/267) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [pre-commit.ci] pre-commit autoupdate (black 24.8.0 → 24.10.0; pre-commit-hooks: v4.6.0 → v5.0.0) [#253](https://github.com/dandi/dandi-schema/pull/253) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 📝 Documentation

- doc: A comment on current identification of URI and missing space into a description string [#265](https://github.com/dandi/dandi-schema/pull/265) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 5

- [@dependabot[bot]](https://github.com/dependabot[bot])
- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Roni Choudhury ([@waxlamp](https://github.com/waxlamp))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.10.4 (Thu Sep 05 2024)

#### 🐛 Bug Fix

- Properly handle failed requests to retrieve the schema [#251](https://github.com/dandi/dandi-schema/pull/251) ([@danlamanna](https://github.com/danlamanna))
- ENH: adopt sanitize_value from dandi-cli and use for sanitization of identifier [#175](https://github.com/dandi/dandi-schema/pull/175) ([@yarikoptic](https://github.com/yarikoptic))
- [pre-commit.ci] pre-commit autoupdate [#243](https://github.com/dandi/dandi-schema/pull/243) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🔩 Dependency Updates

- Declare `typing_extensions` dependency [#248](https://github.com/dandi/dandi-schema/pull/248) ([@jwodder](https://github.com/jwodder))

#### Authors: 4

- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Dan LaManna ([@danlamanna](https://github.com/danlamanna))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.10.3 (Mon Aug 12 2024)

#### 🐛 Bug Fix

- Move pattern specification for `BaseType.identifier` to the annotation for the `str` type [#247](https://github.com/dandi/dandi-schema/pull/247) ([@candleindark](https://github.com/candleindark))

#### Authors: 1

- Isaac To ([@candleindark](https://github.com/candleindark))

---

# 0.10.2 (Wed Jul 10 2024)

#### 🐛 Bug Fix

- Use discriminated unions to provide more helpful error messages [#245](https://github.com/dandi/dandi-schema/pull/245) ([@mvandenburgh](https://github.com/mvandenburgh))
- Set the `$schema` key with the schema dialect [#236](https://github.com/dandi/dandi-schema/pull/236) ([@candleindark](https://github.com/candleindark))
- Add validator to ensure a contact person has email provided [#235](https://github.com/dandi/dandi-schema/pull/235) ([@candleindark](https://github.com/candleindark))

#### 🏠 Internal

- [pre-commit.ci] pre-commit autoupdate [#241](https://github.com/dandi/dandi-schema/pull/241) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#237](https://github.com/dandi/dandi-schema/pull/237) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#234](https://github.com/dandi/dandi-schema/pull/234) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🧪 Tests

- GitHub tests.yml CI: explicitly specify macos-12 and use python 3.11 to test against dandi-cli [#238](https://github.com/dandi/dandi-schema/pull/238) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 4

- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Isaac To ([@candleindark](https://github.com/candleindark))
- Mike VanDenburgh ([@mvandenburgh](https://github.com/mvandenburgh))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.10.1 (Mon Mar 18 2024)

#### 🐛 Bug Fix

- Update auto version number [#233](https://github.com/dandi/dandi-schema/pull/233) ([@satra](https://github.com/satra))
- Add ResourceType enum and associate with Resource model [#232](https://github.com/dandi/dandi-schema/pull/232) ([@bendichter](https://github.com/bendichter) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#229](https://github.com/dandi/dandi-schema/pull/229) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### Authors: 3

- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Ben Dichter ([@bendichter](https://github.com/bendichter))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.10.0 (Mon Feb 12 2024)

#### 🚀 Enhancement

- Remove Zarr checksum code [#217](https://github.com/dandi/dandi-schema/pull/217) ([@jwodder](https://github.com/jwodder))

#### 🐛 Bug Fix

- [pre-commit.ci] pre-commit autoupdate [#219](https://github.com/dandi/dandi-schema/pull/219) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🏠 Internal

- [gh-actions](deps): Bump codecov/codecov-action from 3 to 4 [#222](https://github.com/dandi/dandi-schema/pull/222) ([@dependabot[bot]](https://github.com/dependabot[bot]) [@jwodder](https://github.com/jwodder))

#### 🧪 Tests

- Move `TempKlass`es outside of test functions [#224](https://github.com/dandi/dandi-schema/pull/224) ([@jwodder](https://github.com/jwodder))

#### Authors: 3

- [@dependabot[bot]](https://github.com/dependabot[bot])
- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.9.1 (Tue Jan 30 2024)

#### 🐛 Bug Fix

- Allow dictionary representation of `Dandiset` to have extra attributes [#218](https://github.com/dandi/dandi-schema/pull/218) ([@candleindark](https://github.com/candleindark))

#### 🧪 Tests

- Remove unneeded mark to fixture [#221](https://github.com/dandi/dandi-schema/pull/221) ([@candleindark](https://github.com/candleindark))

#### Authors: 1

- Isaac To ([@candleindark](https://github.com/candleindark))

---

# 0.9.0 (Mon Jan 22 2024)

#### 🚀 Enhancement

- Update to supporting Pydantic V2 [#203](https://github.com/dandi/dandi-schema/pull/203) ([@candleindark](https://github.com/candleindark) [@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🐛 Bug Fix

- [pre-commit.ci] pre-commit autoupdate [#211](https://github.com/dandi/dandi-schema/pull/211) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- Give `version2tuple()` a better type annotation [#208](https://github.com/dandi/dandi-schema/pull/208) ([@jwodder](https://github.com/jwodder))
- Add `__all__` to `__init__.py` [#195](https://github.com/dandi/dandi-schema/pull/195) ([@jwodder](https://github.com/jwodder))
- Remove 3.7 [#193](https://github.com/dandi/dandi-schema/pull/193) ([@yarikoptic](https://github.com/yarikoptic))
- [pre-commit.ci] pre-commit autoupdate [#192](https://github.com/dandi/dandi-schema/pull/192) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#188](https://github.com/dandi/dandi-schema/pull/188) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#186](https://github.com/dandi/dandi-schema/pull/186) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🏎 Performance

- OPT: (memory) cache schema files upon first read from github [#213](https://github.com/dandi/dandi-schema/pull/213) ([@yarikoptic](https://github.com/yarikoptic))

#### 🏠 Internal

- [pre-commit.ci] pre-commit autoupdate [#215](https://github.com/dandi/dandi-schema/pull/215) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [pre-commit.ci] pre-commit autoupdate [#212](https://github.com/dandi/dandi-schema/pull/212) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [gh-actions](deps): Bump actions/setup-python from 4 to 5 [#210](https://github.com/dandi/dandi-schema/pull/210) ([@dependabot[bot]](https://github.com/dependabot[bot]) [@satra](https://github.com/satra))
- Remove `typing_extensions` imports [#207](https://github.com/dandi/dandi-schema/pull/207) ([@jwodder](https://github.com/jwodder))
- Unpin versioningit version [#196](https://github.com/dandi/dandi-schema/pull/196) ([@jwodder](https://github.com/jwodder))
- [pre-commit.ci] pre-commit autoupdate [#200](https://github.com/dandi/dandi-schema/pull/200) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- [gh-actions](deps): Bump actions/checkout from 3 to 4 [#191](https://github.com/dandi/dandi-schema/pull/191) ([@dependabot[bot]](https://github.com/dependabot[bot]))

#### 🧪 Tests

- Rerun failing `test_dandimeta_datacite` tests [#199](https://github.com/dandi/dandi-schema/pull/199) ([@jwodder](https://github.com/jwodder))
- mypy: Set `ignore_missing_imports = False` [#197](https://github.com/dandi/dandi-schema/pull/197) ([@jwodder](https://github.com/jwodder))
- Test against Python 3.12 [#198](https://github.com/dandi/dandi-schema/pull/198) ([@jwodder](https://github.com/jwodder))
- Update README.md - more about use of the library + a few hyperlinks to files and projects [#197](https://github.com/dandi/dandi-schema/pull/197) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 6

- [@dependabot[bot]](https://github.com/dependabot[bot])
- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Isaac To ([@candleindark](https://github.com/candleindark))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.8.4 (Fri Jun 16 2023)

#### 🐛 Bug Fix

- added funderidtype and support for funder and sponsor roles to datacite metadata [#167](https://github.com/dandi/dandi-schema/pull/167) ([@satra](https://github.com/satra) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]) [@djarecka](https://github.com/djarecka))

#### 🧪 Tests

- Add mypy to test extra_requires since needed for type hints testing [#174](https://github.com/dandi/dandi-schema/pull/174) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 4

- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.8.3 (Mon Apr 17 2023)

#### 🏠 Internal

- [pre-commit.ci] pre-commit autoupdate [#170](https://github.com/dandi/dandi-schema/pull/170) ([@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🔩 Dependency Updates

- Restrict pydantic requirement to < 2.0 [#177](https://github.com/dandi/dandi-schema/pull/177) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.8.2 (Thu Mar 16 2023)

#### 🐛 Bug Fix

- fix: add 0.6.3 to validation [#165](https://github.com/dandi/dandi-schema/pull/165) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.8.1 (Mon Mar 06 2023)

#### 🐛 Bug Fix

- Fix type annotation of `unvalidated()` [#163](https://github.com/dandi/dandi-schema/pull/163) ([@jwodder](https://github.com/jwodder))

#### Authors: 1

- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.8.0 (Mon Mar 06 2023)

#### 🚀 Enhancement

- Fully type-annotate and type-check everything [#100](https://github.com/dandi/dandi-schema/pull/100) ([@jwodder](https://github.com/jwodder) [@yarikoptic](https://github.com/yarikoptic))

#### 🐛 Bug Fix

- Use GitHub for Flake8 pre-commit hook [#154](https://github.com/dandi/dandi-schema/pull/154) ([@danlamanna](https://github.com/danlamanna))
- Properly include "data packages" in project [#138](https://github.com/dandi/dandi-schema/pull/138) ([@jwodder](https://github.com/jwodder))

#### 🏠 Internal

- Autoupdate .pre-commit-config.yaml [#161](https://github.com/dandi/dandi-schema/pull/161) ([@jwodder](https://github.com/jwodder))
- Configure Dependabot to update GitHub Actions action versions [#149](https://github.com/dandi/dandi-schema/pull/149) ([@jwodder](https://github.com/jwodder) [@satra](https://github.com/satra))
- Update GitHub Actions to use ubuntu-latest [#150](https://github.com/dandi/dandi-schema/pull/150) ([@jwodder](https://github.com/jwodder))
- Update GitHub Actions action versions [#148](https://github.com/dandi/dandi-schema/pull/148) ([@jwodder](https://github.com/jwodder))
- Set action step outputs via $GITHUB_OUTPUT [#147](https://github.com/dandi/dandi-schema/pull/147) ([@jwodder](https://github.com/jwodder))
- Update pre-commit hooks and rerun [#145](https://github.com/dandi/dandi-schema/pull/145) ([@jwodder](https://github.com/jwodder))
- Update how jsonschema format checkers are retrieved [#146](https://github.com/dandi/dandi-schema/pull/146) ([@jwodder](https://github.com/jwodder))

#### 📝 Documentation

- dandi-schema readme edit [#152](https://github.com/dandi/dandi-schema/pull/152) ([@melster1010](https://github.com/melster1010))

#### 🧪 Tests

- Install dandi's `extras` extra when testing [#162](https://github.com/dandi/dandi-schema/pull/162) ([@jwodder](https://github.com/jwodder))
- Test against Python 3.11 [#151](https://github.com/dandi/dandi-schema/pull/151) ([@jwodder](https://github.com/jwodder))
- Revert "Set DJANGO_DANDI_WEB_APP_URL for dandi-cli integration tests" [#137](https://github.com/dandi/dandi-schema/pull/137) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 5

- Dan LaManna ([@danlamanna](https://github.com/danlamanna))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Mary Elise Dedicke ([@melster1010](https://github.com/melster1010))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.1 (Thu Apr 28 2022)

#### 🐛 Bug Fix

- add 0.6.2 to validation schemas [#133](https://github.com/dandi/dandi-schema/pull/133) ([@satra](https://github.com/satra))

#### 🧪 Tests

- Set DJANGO_DANDI_WEB_APP_URL for dandi-cli integration tests [#132](https://github.com/dandi/dandi-schema/pull/132) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.7.0 (Wed Apr 06 2022)

#### 🚀 Enhancement

- ENH/RF: do not enforce any DANDI instance by default, support DJANGO_DANDI_WEB_APP_URL env var to specify one [#128](https://github.com/dandi/dandischema/pull/128) ([@yarikoptic](https://github.com/yarikoptic))

#### 🧪 Tests

- Directly base Docker image off of dandi-archive image [#126](https://github.com/dandi/dandischema/pull/126) ([@jwodder](https://github.com/jwodder))
- Update dandi-archive Dockerfile to use Python 3.9 [#125](https://github.com/dandi/dandischema/pull/125) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.6.0 (Thu Mar 17 2022)

#### 🚀 Enhancement

- fix: add type of id to hasMember [#123](https://github.com/dandi/dandischema/pull/123) ([@satra](https://github.com/satra))
- Update zarr checksums [#120](https://github.com/dandi/dandischema/pull/120) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.5.3 (Mon Mar 07 2022)

#### 🐛 Bug Fix

- Unify version pattern, allow local dandiset URLs [#121](https://github.com/dandi/dandischema/pull/121) ([@AlmightyYakob](https://github.com/AlmightyYakob) [@satra](https://github.com/satra))

#### Authors: 2

- Jacob Nesbitt ([@AlmightyYakob](https://github.com/AlmightyYakob))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.5.2 (Mon Jan 31 2022)

#### 🐛 Bug Fix

- Specify part generator to DandiETag class [#117](https://github.com/dandi/dandischema/pull/117) ([@AlmightyYakob](https://github.com/AlmightyYakob))
- Define `PartGenerator` default part size as class member [#116](https://github.com/dandi/dandischema/pull/116) ([@AlmightyYakob](https://github.com/AlmightyYakob))

#### Authors: 1

- Jacob Nesbitt ([@AlmightyYakob](https://github.com/AlmightyYakob))

---

# 0.5.1 (Sat Jan 15 2022)

#### 🐛 Bug Fix

- Various edge case fixes [#112](https://github.com/dandi/dandischema/pull/112) ([@satra](https://github.com/satra))
- get_checksum(): Error on empty input [#113](https://github.com/dandi/dandischema/pull/113) ([@jwodder](https://github.com/jwodder))
- adding Orcid ID to the contributors [#111](https://github.com/dandi/dandischema/pull/111) ([@djarecka](https://github.com/djarecka) [@satra](https://github.com/satra))
- Zarr checksum calculation [#109](https://github.com/dandi/dandischema/pull/109) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 4

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.5.0 (Tue Jan 11 2022)

#### 🚀 Enhancement

- fixing to_datacite: more flexible for urls [#107](https://github.com/dandi/dandischema/pull/107) ([@djarecka](https://github.com/djarecka) [@satra](https://github.com/satra))

#### 🐛 Bug Fix

- Add dandi:dandi-zarr-checksum digest [#108](https://github.com/dandi/dandischema/pull/108) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))
- fix: raise validation error on mismatched name [#97](https://github.com/dandi/dandischema/pull/97) ([@satra](https://github.com/satra))
- fix: allows aggregation after discarding path extensions [#105](https://github.com/dandi/dandischema/pull/105) ([@satra](https://github.com/satra))
- fix: address pydantic issue to make value required [#106](https://github.com/dandi/dandischema/pull/106) ([@satra](https://github.com/satra))
- Update versioningit version [#103](https://github.com/dandi/dandischema/pull/103) ([@jwodder](https://github.com/jwodder))

#### 🏠 Internal

- Remove duplicate "requests" dependency [#101](https://github.com/dandi/dandischema/pull/101) ([@jwodder](https://github.com/jwodder))
- Update codecov action to v2 [#95](https://github.com/dandi/dandischema/pull/95) ([@jwodder](https://github.com/jwodder))

#### 🧪 Tests

- Test against Python 3.10 [#99](https://github.com/dandi/dandischema/pull/99) ([@jwodder](https://github.com/jwodder))

#### Authors: 4

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.4.3 (Thu Oct 07 2021)

#### 🐛 Bug Fix

- enh: add subject and sample aggregating for bids dandisets [#92](https://github.com/dandi/dandischema/pull/92) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.4.2 (Mon Oct 04 2021)

#### 🐛 Bug Fix

- fix: associate schema key with schemas for older versions [#91](https://github.com/dandi/dandischema/pull/91) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.4.1 (Tue Sep 28 2021)

#### 🐛 Bug Fix

- Better exception classes [#89](https://github.com/dandi/dandischema/pull/89) ([@dchiquito](https://github.com/dchiquito))

#### 🧪 Tests

- Mark tests requiring network access and add a test workflow that disables network access [#88](https://github.com/dandi/dandischema/pull/88) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.4.0 (Sun Sep 26 2021)

#### 🚀 Enhancement

- Release 0.6.0 [#86](https://github.com/dandi/dandischema/pull/86) ([@satra](https://github.com/satra))

#### 🐛 Bug Fix

- adds all properties to context with implicit dandi schema [#84](https://github.com/dandi/dandischema/pull/84) ([@satra](https://github.com/satra))
- make schemaKey required and improve validation and migration functions [#77](https://github.com/dandi/dandischema/pull/77) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))
- [fix] creating identifier from url in relatedResource [#78](https://github.com/dandi/dandischema/pull/78) ([@djarecka](https://github.com/djarecka) [@satra](https://github.com/satra))

#### Authors: 3

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.3.4 (Wed Sep 15 2021)

#### 🐛 Bug Fix

- remove NC license [#83](https://github.com/dandi/dandischema/pull/83) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.3.3 (Thu Sep 09 2021)

#### 🐛 Bug Fix

- fixing to_datacie, allowing for None in roleName [#81](https://github.com/dandi/dandischema/pull/81) ([@djarecka](https://github.com/djarecka))

#### 🏠 Internal

- Switch to versioningit (non-src-layout) [#56](https://github.com/dandi/dandischema/pull/56) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.3.2 (Thu Jul 29 2021)

#### 🐛 Bug Fix

- Datacite publish argument [#70](https://github.com/dandi/dandischema/pull/70) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 1

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))

---

# 0.3.1 (Wed Jul 28 2021)

#### 🐛 Bug Fix

- ensure schemaKeys are set properly [#68](https://github.com/dandi/dandischema/pull/68) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.3.0 (Wed Jul 28 2021)

#### 🚀 Enhancement

- improve help options [#60](https://github.com/dandi/dandischema/pull/60) ([@satra](https://github.com/satra))
- Copy dandietag code from dandi-cli [#58](https://github.com/dandi/dandischema/pull/58) ([@jwodder](https://github.com/jwodder))
- fix: clean up optional components of the schema [#52](https://github.com/dandi/dandischema/pull/52) ([@satra](https://github.com/satra))

#### 🐛 Bug Fix

- Use a generic DOI site instead of 10.80507 [#65](https://github.com/dandi/dandischema/pull/65) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))

#### ⚠️ Pushed to `master`

- BF: do not refer to dandi-cli for LICENSE file ([@yarikoptic](https://github.com/yarikoptic))

#### 🧪 Tests

- Set DANDI_ALLOW_LOCALHOST_URLS when running dandi-cli tests [#66](https://github.com/dandi/dandischema/pull/66) ([@jwodder](https://github.com/jwodder))
- RF(CI): run dandi-cli tests only against 3.8 (but all OSes) [#64](https://github.com/dandi/dandischema/pull/64) ([@yarikoptic](https://github.com/yarikoptic))
- Run dandi-cli tests with dandi-api image built with local version of dandischema [#63](https://github.com/dandi/dandischema/pull/63) ([@jwodder](https://github.com/jwodder))
- fix: change id to identifier for software [#46](https://github.com/dandi/dandischema/pull/46) ([@satra](https://github.com/satra))
- Add workflow for testing dandischema against latest release of dandi-cli [#49](https://github.com/dandi/dandischema/pull/49) ([@jwodder](https://github.com/jwodder))

#### Authors: 4

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.10 (Wed Jun 30 2021)

#### 🐛 Bug Fix

- enh: allow checking to see data are matched but allow for missing fields [#48](https://github.com/dandi/dandischema/pull/48) ([@satra](https://github.com/satra))
- adding AgeReferenceType [#50](https://github.com/dandi/dandischema/pull/50) ([@djarecka](https://github.com/djarecka))

#### Authors: 2

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.9 (Thu Jun 24 2021)

#### 🐛 Bug Fix

- doc: add a bit more info to readme [#45](https://github.com/dandi/dandischema/pull/45) ([@satra](https://github.com/satra))
- release.yml: Use DANDI_GITHUB_TOKEN to push to repo [#44](https://github.com/dandi/dandischema/pull/44) ([@jwodder](https://github.com/jwodder))
- enh: update models to do more validation checks [#42](https://github.com/dandi/dandischema/pull/42) ([@satra](https://github.com/satra))

#### 🏠 Internal

- Add flake8 to .pre-commit-config.taml [#39](https://github.com/dandi/dandischema/pull/39) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.8 (Fri Jun 18 2021)

#### 🐛 Bug Fix

- Fix: Make the library more robust for publishing [#41](https://github.com/dandi/dandischema/pull/41) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.7 (Thu Jun 17 2021)

#### 🐛 Bug Fix

- fix: allow migration for versions greater than 0.3.2 [#40](https://github.com/dandi/dandischema/pull/40) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.6 (Wed Jun 16 2021)

#### 🐛 Bug Fix

- fix: make assetsummary computable for dandisets with no assets [#38](https://github.com/dandi/dandischema/pull/38) ([@satra](https://github.com/satra) [@dchiquito](https://github.com/dchiquito))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.5 (Wed Jun 16 2021)

#### 🐛 Bug Fix

- enh: implement metadata aggregator for asset summary [#34](https://github.com/dandi/dandischema/pull/34) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))
- Only attempt to remove contributorType if present [#37](https://github.com/dandi/dandischema/pull/37) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 3

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.4 (Thu Jun 10 2021)

#### 🐛 Bug Fix

- Allow location fields to have localhost URLs [#33](https://github.com/dandi/dandischema/pull/33) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 1

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))

---

# 0.2.3 (Wed Jun 09 2021)

#### 🐛 Bug Fix

- fix: update migration code to account for missing fields [#30](https://github.com/dandi/dandischema/pull/30) ([@satra](https://github.com/satra))

#### 🏠 Internal

- Use DANDI_GITHUB_TOKEN to check out dandi/schema when releasing [#31](https://github.com/dandi/dandischema/pull/31) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.2 (Tue Jun 08 2021)

#### 🐛 Bug Fix

- fix: remove readOnly from constants [#28](https://github.com/dandi/dandischema/pull/28) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.1 (Fri May 28 2021)

#### 🐛 Bug Fix

- fix: dandi-etag carries extra component beyond md5 [#24](https://github.com/dandi/dandischema/pull/24) ([@satra](https://github.com/satra))

#### 🏠 Internal

- Add missing "working-directory" [#27](https://github.com/dandi/dandischema/pull/27) ([@jwodder](https://github.com/jwodder))
- Delete schema-* tags before running auto [#26](https://github.com/dandi/dandischema/pull/26) ([@jwodder](https://github.com/jwodder))
- Fix release workflow [#25](https://github.com/dandi/dandischema/pull/25) ([@jwodder](https://github.com/jwodder))
- Patch versioneer to exclude tags that don't start with a digit [#20](https://github.com/dandi/dandischema/pull/20) ([@jwodder](https://github.com/jwodder))

#### 🧪 Tests

- Set up schema testing and autorelease of new schemata [#17](https://github.com/dandi/dandischema/pull/17) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.1 (Fri May 28 2021)

#### 🐛 Bug Fix

- fix: dandi-etag carries extra component beyond md5 [#24](https://github.com/dandi/dandischema/pull/24) ([@satra](https://github.com/satra))

#### 🏠 Internal

- Fix release workflow [#25](https://github.com/dandi/dandischema/pull/25) ([@jwodder](https://github.com/jwodder))
- Patch versioneer to exclude tags that don't start with a digit [#20](https://github.com/dandi/dandischema/pull/20) ([@jwodder](https://github.com/jwodder))

#### 🧪 Tests

- Set up schema testing and autorelease of new schemata [#17](https://github.com/dandi/dandischema/pull/17) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.0 (Wed May 26 2021)

#### 🚀 Enhancement

- ENH: support migration, validation, schema improvements [#6](https://github.com/dandi/dandischema/pull/6) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### 🐛 Bug Fix

- Fix/schemakey metaclass [#13](https://github.com/dandi/dandischema/pull/13) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.1.1 (Tue May 25 2021)

#### 🏠 Internal

- RF(TEMP): disable publishing new versions of schemata [#11](https://github.com/dandi/dandischema/pull/11) ([@yarikoptic](https://github.com/yarikoptic))
- Pin auto version [#10](https://github.com/dandi/dandischema/pull/10) ([@jwodder](https://github.com/jwodder))
- Include CHANGELOG.md and tox.ini in sdists [#8](https://github.com/dandi/dandischema/pull/8) ([@jwodder](https://github.com/jwodder))

#### 📝 Documentation

- Start CHANGELOG [#1](https://github.com/dandi/dandischema/pull/1) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.1.0 (2021-05-20)

Initial release (after splitting code off from
[dandi](https://github.com/dandi/dandi-cli))
