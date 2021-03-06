# 0.7.1 (Thu Apr 28 2022)

#### ๐ Bug Fix

- add 0.6.2 to validation schemas [#133](https://github.com/dandi/dandi-schema/pull/133) ([@satra](https://github.com/satra))

#### ๐งช Tests

- Set DJANGO_DANDI_WEB_APP_URL for dandi-cli integration tests [#132](https://github.com/dandi/dandi-schema/pull/132) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.7.0 (Wed Apr 06 2022)

#### ๐ Enhancement

- ENH/RF: do not enforce any DANDI instance by default, support DJANGO_DANDI_WEB_APP_URL env var to specify one [#128](https://github.com/dandi/dandischema/pull/128) ([@yarikoptic](https://github.com/yarikoptic))

#### ๐งช Tests

- Directly base Docker image off of dandi-archive image [#126](https://github.com/dandi/dandischema/pull/126) ([@jwodder](https://github.com/jwodder))
- Update dandi-archive Dockerfile to use Python 3.9 [#125](https://github.com/dandi/dandischema/pull/125) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.6.0 (Thu Mar 17 2022)

#### ๐ Enhancement

- fix: add type of id to hasMember [#123](https://github.com/dandi/dandischema/pull/123) ([@satra](https://github.com/satra))
- Update zarr checksums [#120](https://github.com/dandi/dandischema/pull/120) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.5.3 (Mon Mar 07 2022)

#### ๐ Bug Fix

- Unify version pattern, allow local dandiset URLs [#121](https://github.com/dandi/dandischema/pull/121) ([@AlmightyYakob](https://github.com/AlmightyYakob) [@satra](https://github.com/satra))

#### Authors: 2

- Jacob Nesbitt ([@AlmightyYakob](https://github.com/AlmightyYakob))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.5.2 (Mon Jan 31 2022)

#### ๐ Bug Fix

- Specify part generator to DandiETag class [#117](https://github.com/dandi/dandischema/pull/117) ([@AlmightyYakob](https://github.com/AlmightyYakob))
- Define `PartGenerator` default part size as class member [#116](https://github.com/dandi/dandischema/pull/116) ([@AlmightyYakob](https://github.com/AlmightyYakob))

#### Authors: 1

- Jacob Nesbitt ([@AlmightyYakob](https://github.com/AlmightyYakob))

---

# 0.5.1 (Sat Jan 15 2022)

#### ๐ Bug Fix

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

#### ๐ Enhancement

- fixing to_datacite: more flexible for urls [#107](https://github.com/dandi/dandischema/pull/107) ([@djarecka](https://github.com/djarecka) [@satra](https://github.com/satra))

#### ๐ Bug Fix

- Add dandi:dandi-zarr-checksum digest [#108](https://github.com/dandi/dandischema/pull/108) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))
- fix: raise validation error on mismatched name [#97](https://github.com/dandi/dandischema/pull/97) ([@satra](https://github.com/satra))
- fix: allows aggregation after discarding path extensions [#105](https://github.com/dandi/dandischema/pull/105) ([@satra](https://github.com/satra))
- fix: address pydantic issue to make value required [#106](https://github.com/dandi/dandischema/pull/106) ([@satra](https://github.com/satra))
- Update versioningit version [#103](https://github.com/dandi/dandischema/pull/103) ([@jwodder](https://github.com/jwodder))

#### ๐? Internal

- Remove duplicate "requests" dependency [#101](https://github.com/dandi/dandischema/pull/101) ([@jwodder](https://github.com/jwodder))
- Update codecov action to v2 [#95](https://github.com/dandi/dandischema/pull/95) ([@jwodder](https://github.com/jwodder))

#### ๐งช Tests

- Test against Python 3.10 [#99](https://github.com/dandi/dandischema/pull/99) ([@jwodder](https://github.com/jwodder))

#### Authors: 4

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.4.3 (Thu Oct 07 2021)

#### ๐ Bug Fix

- enh: add subject and sample aggregating for bids dandisets [#92](https://github.com/dandi/dandischema/pull/92) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.4.2 (Mon Oct 04 2021)

#### ๐ Bug Fix

- fix: associate schema key with schemas for older versions [#91](https://github.com/dandi/dandischema/pull/91) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.4.1 (Tue Sep 28 2021)

#### ๐ Bug Fix

- Better exception classes [#89](https://github.com/dandi/dandischema/pull/89) ([@dchiquito](https://github.com/dchiquito))

#### ๐งช Tests

- Mark tests requiring network access and add a test workflow that disables network access [#88](https://github.com/dandi/dandischema/pull/88) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.4.0 (Sun Sep 26 2021)

#### ๐ Enhancement

- Release 0.6.0 [#86](https://github.com/dandi/dandischema/pull/86) ([@satra](https://github.com/satra))

#### ๐ Bug Fix

- adds all properties to context with implicit dandi schema [#84](https://github.com/dandi/dandischema/pull/84) ([@satra](https://github.com/satra))
- make schemaKey required and improve validation and migration functions [#77](https://github.com/dandi/dandischema/pull/77) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))
- [fix] creating identifier from url in relatedResource [#78](https://github.com/dandi/dandischema/pull/78) ([@djarecka](https://github.com/djarecka) [@satra](https://github.com/satra))

#### Authors: 3

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.3.4 (Wed Sep 15 2021)

#### ๐ Bug Fix

- remove NC license [#83](https://github.com/dandi/dandischema/pull/83) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.3.3 (Thu Sep 09 2021)

#### ๐ Bug Fix

- fixing to_datacie, allowing for None in roleName [#81](https://github.com/dandi/dandischema/pull/81) ([@djarecka](https://github.com/djarecka))

#### ๐? Internal

- Switch to versioningit (non-src-layout) [#56](https://github.com/dandi/dandischema/pull/56) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))

---

# 0.3.2 (Thu Jul 29 2021)

#### ๐ Bug Fix

- Datacite publish argument [#70](https://github.com/dandi/dandischema/pull/70) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 1

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))

---

# 0.3.1 (Wed Jul 28 2021)

#### ๐ Bug Fix

- ensure schemaKeys are set properly [#68](https://github.com/dandi/dandischema/pull/68) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.3.0 (Wed Jul 28 2021)

#### ๐ Enhancement

- improve help options [#60](https://github.com/dandi/dandischema/pull/60) ([@satra](https://github.com/satra))
- Copy dandietag code from dandi-cli [#58](https://github.com/dandi/dandischema/pull/58) ([@jwodder](https://github.com/jwodder))
- fix: clean up optional components of the schema [#52](https://github.com/dandi/dandischema/pull/52) ([@satra](https://github.com/satra))

#### ๐ Bug Fix

- Use a generic DOI site instead of 10.80507 [#65](https://github.com/dandi/dandischema/pull/65) ([@dchiquito](https://github.com/dchiquito) [@satra](https://github.com/satra))

#### โ?๏ธ Pushed to `master`

- BF: do not refer to dandi-cli for LICENSE file ([@yarikoptic](https://github.com/yarikoptic))

#### ๐งช Tests

- Set DANDI_ALLOW_LOCALHOST_URLS when running dandi-cli tests [#66](https://github.com/dandi/dandischema/pull/66) ([@jwodder](https://github.com/jwodder))
- RF(CI): run dandi-cli tests only against 3.8 (but all OSes) [#64](https://github.com/dandi/dandischema/pull/64) ([@yarikoptic](https://github.com/yarikoptic))
- Run dandi-cli tests with dandi-api image built with local version of dandischema [#63](https://github.com/dandi/dandischema/pull/63) ([@jwodder](https://github.com/jwodder))
- fix: change id to indentifier for software [#46](https://github.com/dandi/dandischema/pull/46) ([@satra](https://github.com/satra))
- Add workflow for testing dandischema against latest release of dandi-cli [#49](https://github.com/dandi/dandischema/pull/49) ([@jwodder](https://github.com/jwodder))

#### Authors: 4

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.10 (Wed Jun 30 2021)

#### ๐ Bug Fix

- enh: allow checking to see data are matched but allow for missing fields [#48](https://github.com/dandi/dandischema/pull/48) ([@satra](https://github.com/satra))
- adding AgeReferenceType [#50](https://github.com/dandi/dandischema/pull/50) ([@djarecka](https://github.com/djarecka))

#### Authors: 2

- Dorota Jarecka ([@djarecka](https://github.com/djarecka))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.9 (Thu Jun 24 2021)

#### ๐ Bug Fix

- doc: add a bit more info to readme [#45](https://github.com/dandi/dandischema/pull/45) ([@satra](https://github.com/satra))
- release.yml: Use DANDI_GITHUB_TOKEN to push to repo [#44](https://github.com/dandi/dandischema/pull/44) ([@jwodder](https://github.com/jwodder))
- enh: update models to do more validation checks [#42](https://github.com/dandi/dandischema/pull/42) ([@satra](https://github.com/satra))

#### ๐? Internal

- Add flake8 to .pre-commit-config.taml [#39](https://github.com/dandi/dandischema/pull/39) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.8 (Fri Jun 18 2021)

#### ๐ Bug Fix

- Fix: Make the library more robust for publishing [#41](https://github.com/dandi/dandischema/pull/41) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.7 (Thu Jun 17 2021)

#### ๐ Bug Fix

- fix: allow migration for versions greater than 0.3.2 [#40](https://github.com/dandi/dandischema/pull/40) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.6 (Wed Jun 16 2021)

#### ๐ Bug Fix

- fix: make assetsummary computable for dandisets with no assets [#38](https://github.com/dandi/dandischema/pull/38) ([@satra](https://github.com/satra) [@dchiquito](https://github.com/dchiquito))

#### Authors: 2

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.5 (Wed Jun 16 2021)

#### ๐ Bug Fix

- enh: implement metadata aggregator for asset summary [#34](https://github.com/dandi/dandischema/pull/34) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))
- Only attempt to remove contributorType if present [#37](https://github.com/dandi/dandischema/pull/37) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 3

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))
- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.2.4 (Thu Jun 10 2021)

#### ๐ Bug Fix

- Allow location fields to have localhost URLs [#33](https://github.com/dandi/dandischema/pull/33) ([@dchiquito](https://github.com/dchiquito))

#### Authors: 1

- Daniel Chiquito ([@dchiquito](https://github.com/dchiquito))

---

# 0.2.3 (Wed Jun 09 2021)

#### ๐ Bug Fix

- fix: update migration code to account for missing fields [#30](https://github.com/dandi/dandischema/pull/30) ([@satra](https://github.com/satra))

#### ๐? Internal

- Use DANDI_GITHUB_TOKEN to check out dandi/schema when releasing [#31](https://github.com/dandi/dandischema/pull/31) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.2 (Tue Jun 08 2021)

#### ๐ Bug Fix

- fix: remove readOnly from constants [#28](https://github.com/dandi/dandischema/pull/28) ([@satra](https://github.com/satra))

#### Authors: 1

- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.1 (Fri May 28 2021)

#### ๐ Bug Fix

- fix: dandi-etag carries extra component beyond md5 [#24](https://github.com/dandi/dandischema/pull/24) ([@satra](https://github.com/satra))

#### ๐? Internal

- Add missing "working-directory" [#27](https://github.com/dandi/dandischema/pull/27) ([@jwodder](https://github.com/jwodder))
- Delete schema-* tags before running auto [#26](https://github.com/dandi/dandischema/pull/26) ([@jwodder](https://github.com/jwodder))
- Fix release workflow [#25](https://github.com/dandi/dandischema/pull/25) ([@jwodder](https://github.com/jwodder))
- Patch versioneer to exclude tags that don't start with a digit [#20](https://github.com/dandi/dandischema/pull/20) ([@jwodder](https://github.com/jwodder))

#### ๐งช Tests

- Set up schema testing and autorelease of new schemata [#17](https://github.com/dandi/dandischema/pull/17) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.1 (Fri May 28 2021)

#### ๐ Bug Fix

- fix: dandi-etag carries extra component beyond md5 [#24](https://github.com/dandi/dandischema/pull/24) ([@satra](https://github.com/satra))

#### ๐? Internal

- Fix release workflow [#25](https://github.com/dandi/dandischema/pull/25) ([@jwodder](https://github.com/jwodder))
- Patch versioneer to exclude tags that don't start with a digit [#20](https://github.com/dandi/dandischema/pull/20) ([@jwodder](https://github.com/jwodder))

#### ๐งช Tests

- Set up schema testing and autorelease of new schemata [#17](https://github.com/dandi/dandischema/pull/17) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Satrajit Ghosh ([@satra](https://github.com/satra))

---

# 0.2.0 (Wed May 26 2021)

#### ๐ Enhancement

- ENH: support migration, validation, schema improvements [#6](https://github.com/dandi/dandischema/pull/6) ([@satra](https://github.com/satra) [@yarikoptic](https://github.com/yarikoptic))

#### ๐ Bug Fix

- Fix/schemakey metaclass [#13](https://github.com/dandi/dandischema/pull/13) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Satrajit Ghosh ([@satra](https://github.com/satra))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.1.1 (Tue May 25 2021)

#### ๐? Internal

- RF(TEMP): disable publishing new versions of schemata [#11](https://github.com/dandi/dandischema/pull/11) ([@yarikoptic](https://github.com/yarikoptic))
- Pin auto version [#10](https://github.com/dandi/dandischema/pull/10) ([@jwodder](https://github.com/jwodder))
- Include CHANGELOG.md and tox.ini in sdists [#8](https://github.com/dandi/dandischema/pull/8) ([@jwodder](https://github.com/jwodder))

#### ๐ Documentation

- Start CHANGELOG [#1](https://github.com/dandi/dandischema/pull/1) ([@jwodder](https://github.com/jwodder))

#### Authors: 2

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.1.0 (2021-05-20)

Initial release (after splitting code off from
[dandi](https://github.com/dandi/dandi-cli))
