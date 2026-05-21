# Changelog

All notable changes to this project will be documented in this file. See [Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [0.135.0](https://github.com/eg-internal/querybook/compare/v0.134.0...v0.135.0) (2026-05-21)


### Features

* add github sync with authorization through MCP ([#543](https://github.com/eg-internal/querybook/issues/543)) ([122e51d](https://github.com/eg-internal/querybook/commit/122e51df4d39adeb70160118fed7e184d7e68387))
* **metastore:** UC sandbox schema filter with per-user scoping ([#541](https://github.com/eg-internal/querybook/issues/541)) ([241de17](https://github.com/eg-internal/querybook/commit/241de1721051f191210f14fcaeb5bb3c0ba13f4e))
* **tables:** catalog-grouped table menu with 3-level tree view ([#542](https://github.com/eg-internal/querybook/issues/542)) ([5c3d00c](https://github.com/eg-internal/querybook/commit/5c3d00c93042eb165ce758f5b270c3c70f669e81))


### Bug Fixes

* Fix null and empty catalogs ([#544](https://github.com/eg-internal/querybook/issues/544)) ([f3c829a](https://github.com/eg-internal/querybook/commit/f3c829a9d87ebad69e56c7c70c0ede7ef56d0b44))

## [0.134.0](https://github.com/eg-internal/querybook/compare/v0.133.1...v0.134.0) (2026-05-11)


### Features

* **mcp:** Add OAuth/OIDC authentication via Okta ([3cb51b0](https://github.com/eg-internal/querybook/commit/3cb51b061f7256bae3439d7d9f4278fc22ef9cde))


### Bug Fixes

* Querybook MCP - Update the Auth Deprecation Notice ([#535](https://github.com/eg-internal/querybook/issues/535)) ([5b79f39](https://github.com/eg-internal/querybook/commit/5b79f39717f9f98d8c118b8c8eb2663a1033a7fd))

## [0.133.1](https://github.com/eg-internal/querybook/compare/v0.133.0...v0.133.1) (2026-05-08)


### Bug Fixes

* Databricks metastore OIDC Fix ([#536](https://github.com/eg-internal/querybook/issues/536)) ([693fb8d](https://github.com/eg-internal/querybook/commit/693fb8deae7c265c34b73b7efa0fa357268d23ee))

## [0.133.0](https://github.com/eg-internal/querybook/compare/v0.132.0...v0.133.0) (2026-05-07)


### Features

* Add auth deprecation notice to Querybook MCP server ([1c05276](https://github.com/eg-internal/querybook/commit/1c052763437022b5beec012033878a3f2818d89d))
* **databricks:** add OIDC workload identity federation auth support ([#533](https://github.com/eg-internal/querybook/issues/533)) ([faa0bac](https://github.com/eg-internal/querybook/commit/faa0bac1040a7996d4acc95b92ea37f9ff0f3a2f))

## [0.132.0](https://github.com/eg-internal/querybook/compare/v0.131.2...v0.132.0) (2026-04-15)


### Features

* AI Assistant updates for newer models. ([72fdbea](https://github.com/eg-internal/querybook/commit/72fdbea873efbacf91a57fd996d705d3ac412e77))
* **mcp:** Add static resource guide for discovering resource templates ([e4f05bb](https://github.com/eg-internal/querybook/commit/e4f05bb1c758bc18b778c1314e3a92b14e505111))


### Bug Fixes

* Add eg-data-product as Dataset Tags ([#523](https://github.com/eg-internal/querybook/issues/523)) ([2cdd0eb](https://github.com/eg-internal/querybook/commit/2cdd0ebeb4cbbe289e232bdc28e21c06b1dc1fe3))
* Handle statement-execution resource with no data ([47d4205](https://github.com/eg-internal/querybook/commit/47d4205fed8a70c706d453e675069d468a2b73f9))
* **mcp:** Include query execution errors in MCP resource responses ([5c749eb](https://github.com/eg-internal/querybook/commit/5c749ebe01af9089815d3b9195ffa31ba4463706))
* **mcp:** Log correct uid for resource-guide reads ([9228daf](https://github.com/eg-internal/querybook/commit/9228dafce6e0a23c8f55665b055b322c9981f39a))
* **mcp:** Only apply running filter when running=true in list_query_executions ([f26468c](https://github.com/eg-internal/querybook/commit/f26468cd7ea35fcc261d18d44982935757d30781))
* Template query variables in MCP run_datadoc_cell ([#528](https://github.com/eg-internal/querybook/issues/528)) ([8a03ef0](https://github.com/eg-internal/querybook/commit/8a03ef0ffb5f3a438d3103fef54067fb8fb9bee4))

## [0.131.2](https://github.com/eg-internal/querybook/compare/v0.131.1...v0.131.2) (2026-03-26)


### Bug Fixes

* Add MCP execution metadata and Client Tagging ([42dd970](https://github.com/eg-internal/querybook/commit/42dd970872e19b0d2ba9d085b5c8d354b45a3fb9))
* MCP tools for DataDoc cells now return the cell contents only ([549907c](https://github.com/eg-internal/querybook/commit/549907ca88d6a863a1219a72cc6d6cade3e7e105))

## [0.131.1](https://github.com/eg-internal/querybook/compare/v0.131.0...v0.131.1) (2026-03-26)


### Bug Fixes

* Fix MCP Event Logging and add DataDoc variable support ([bfcb1c7](https://github.com/eg-internal/querybook/commit/bfcb1c768397c2bace64907009109fd7725c8c0d))

## [0.131.0](https://github.com/eg-internal/querybook/compare/v0.130.1...v0.131.0) (2026-03-19)


### Features

* Add ad hoc executions & downloads to MCP server ([f8205f5](https://github.com/eg-internal/querybook/commit/f8205f5de605a5a0b68894e5393ef950196795b6))
* Combo Metastore Loader ([#514](https://github.com/eg-internal/querybook/issues/514)) ([7ac1c65](https://github.com/eg-internal/querybook/commit/7ac1c65f1db43d8eec23887e0bee7433b21bb4e0))

## [0.130.1](https://github.com/eg-internal/querybook/compare/v0.130.0...v0.130.1) (2026-03-13)


### Bug Fixes

* Add prod_mcp service without watchmedo ([d24c816](https://github.com/eg-internal/querybook/commit/d24c816c8744b378b6e294fe0fd0fc703110c4cb))

## [0.130.0](https://github.com/eg-internal/querybook/compare/v0.129.0...v0.130.0) (2026-03-12)


### Features

* Add Catalog Strict Filter Pattern to ACL ([#511](https://github.com/eg-internal/querybook/issues/511)) ([a58f26f](https://github.com/eg-internal/querybook/commit/a58f26f22ff9d98c6bebe50913e2f252c8817ac9))
* EG Specific Databricks and Glue Metastore Loaders ([#506](https://github.com/eg-internal/querybook/issues/506)) ([c7624f6](https://github.com/eg-internal/querybook/commit/c7624f627e24b28a648b04fe3b93d27b349d17cc))
* Querybook MCP Server ([#505](https://github.com/eg-internal/querybook/issues/505)) ([f30c629](https://github.com/eg-internal/querybook/commit/f30c6292558ebc2f8c9acbb2f417c7e172d02ff9))


### Bug Fixes

* Add CLAUDE.md and .claude/context/ files ([#507](https://github.com/eg-internal/querybook/issues/507)) ([5b1f88d](https://github.com/eg-internal/querybook/commit/5b1f88db0fbbe9b264e728d4c78c925aecec85b2))
* Fix catalog support migration issues ([#508](https://github.com/eg-internal/querybook/issues/508)) ([46d69a3](https://github.com/eg-internal/querybook/commit/46d69a3a6a539e51f2e535cc5695210d022efd80))
* Track EGMP / Pulse clicks ([51b9bf0](https://github.com/eg-internal/querybook/commit/51b9bf01e170cd852b184f8626c6eacd8faa767e))
* Update Ava branding to match ([1626ea8](https://github.com/eg-internal/querybook/commit/1626ea85956ddc0590c4baa518bf95e6e06acbbf))
* Update EGMP/Pulse branding on landing page ([7811254](https://github.com/eg-internal/querybook/commit/78112544c0dd90d683e561be998565fe4cbd8a5c))

## [0.129.0](https://github.com/eg-internal/querybook/compare/v0.128.0...v0.129.0) (2026-02-23)


### Features

* Catalog Implementation ([#496](https://github.com/eg-internal/querybook/issues/496)) ([e18fc46](https://github.com/eg-internal/querybook/commit/e18fc465850e53e883620029740bf9231535c0d9))

## [0.128.0](https://github.com/eg-internal/querybook/compare/v0.127.0...v0.128.0) (2026-02-17)


### Features

* Add EGMP and EG Pulse to Landing page ([238881b](https://github.com/eg-internal/querybook/commit/238881bbbcaa468213ea057509cd37349800c1eb))

## [0.127.0](https://github.com/eg-internal/querybook/compare/v0.126.0...v0.127.0) (2026-02-17)


### Features

* Revert "feat: Disable UI access to create API tokens" ([116d21e](https://github.com/eg-internal/querybook/commit/116d21e86ade418452b7591b1ea41ececad946ec))
* Upgrade EG internal certificates ([951ad4e](https://github.com/eg-internal/querybook/commit/951ad4e3c3a448e791402e9062a5cda7d3169826))


### Bug Fixes

* add logging for datadoc schedule execution notifications ([#497](https://github.com/eg-internal/querybook/issues/497)) ([5aec0a7](https://github.com/eg-internal/querybook/commit/5aec0a7f1aeb9912e12d0e86ea81a488c906b04a))
* Fix issue with square UserAvatars in Firefox ([b72c107](https://github.com/eg-internal/querybook/commit/b72c107a9ac6cad9530c50b9881f2b5f69b2590f))

## [0.126.0](https://github.com/eg-internal/querybook/compare/v0.125.2...v0.126.0) (2025-12-11)


### Features

* add task to cleanup orphaned schedules ([#494](https://github.com/eg-internal/querybook/issues/494)) ([a6c4bc7](https://github.com/eg-internal/querybook/commit/a6c4bc7c154623ece3d08e3da4c5aa0b435e7030))
* added cleanup tasks for users removed from environments ([#491](https://github.com/eg-internal/querybook/issues/491)) ([ce01052](https://github.com/eg-internal/querybook/commit/ce010527a5848747399bed01990cb252180e5443))


### Bug Fixes

* Update JIRA links ([2a66396](https://github.com/eg-internal/querybook/commit/2a66396f0afc6992074803cb6d5c8ca29490c54c))
* use correct indexing for 'Run All From Here', and update when it changes ([#495](https://github.com/eg-internal/querybook/issues/495)) ([270fa28](https://github.com/eg-internal/querybook/commit/270fa282e7272651123aa217f5c0f81118f57320))

## [0.125.2](https://github.com/eg-internal/querybook/compare/v0.125.1...v0.125.2) (2025-11-21)


### Bug Fixes

* Rollback Trino client version upgrade ([e63f24b](https://github.com/eg-internal/querybook/commit/e63f24b43bc28660e9a8a315186a68cb9f264efd))

## [0.125.1](https://github.com/eg-internal/querybook/compare/v0.125.0...v0.125.1) (2025-11-19)


### Bug Fixes

* group_id error and add logs for prod/test ([#487](https://github.com/eg-internal/querybook/issues/487)) ([3583138](https://github.com/eg-internal/querybook/commit/35831389743961cb0a36f7fd0901a03bb86e8622))

## [0.125.0](https://github.com/eg-internal/querybook/compare/v0.124.0...v0.125.0) (2025-11-19)


### Features

* Create Databricks Metastore Loader ([#483](https://github.com/eg-internal/querybook/issues/483)) ([c981b20](https://github.com/eg-internal/querybook/commit/c981b20e2a18f40f1695607a5317e0de43bb5d6f))
* Upgrade to Elasticsearch 8.18 ([05c53a3](https://github.com/eg-internal/querybook/commit/05c53a3b69beb2d3deeacb7a9bf90380971de2df))


### Bug Fixes

* separate recursive logic so sqlalchemy compiles correctly ([ec55de6](https://github.com/eg-internal/querybook/commit/ec55de68d4b747075051f1a9e7651e25fc882a40))

## [0.124.0](https://github.com/eg-internal/querybook/compare/v0.123.4...v0.124.0) (2025-11-13)


### Features

* Add friendly Trino Gateway error message ([c8f51f8](https://github.com/eg-internal/querybook/commit/c8f51f81e8bc98e746a481e95303daa4bbbff9c8))


### Bug Fixes

* Update client logic for trino client versions &gt;= 0.326.0 ([#482](https://github.com/eg-internal/querybook/issues/482)) ([eecfbd4](https://github.com/eg-internal/querybook/commit/eecfbd46e3097e55bb0be03e9f78ed280e4ab58c))

## [0.123.4](https://github.com/eg-internal/querybook/compare/v0.123.3...v0.123.4) (2025-11-11)


### Bug Fixes

* update trino version ([#478](https://github.com/eg-internal/querybook/issues/478)) ([ebd9d8a](https://github.com/eg-internal/querybook/commit/ebd9d8a4f46f4189f798bfef32aee30f700fe4d3))

## [0.123.3](https://github.com/eg-internal/querybook/compare/v0.123.2...v0.123.3) (2025-11-06)


### Bug Fixes

* fix shared list page filters ([#475](https://github.com/eg-internal/querybook/issues/475)) ([bbb3000](https://github.com/eg-internal/querybook/commit/bbb300044de2aaece29e0d370070061c18a62243))

## [0.123.2](https://github.com/eg-internal/querybook/compare/v0.123.1...v0.123.2) (2025-11-04)


### Bug Fixes

* Pin python-socketio to fix run_datadoc.py emit ([b89216a](https://github.com/eg-internal/querybook/commit/b89216a0bfb781c2a8a0d737b249183a2f7bfbb7))

## [0.123.1](https://github.com/eg-internal/querybook/compare/v0.123.0...v0.123.1) (2025-10-27)


### Bug Fixes

* Add Teradata count to personalized cost dashboard ([9c6424f](https://github.com/eg-internal/querybook/commit/9c6424f1fd49d3896217bbbff685020890432fb6))

## [0.123.0](https://github.com/eg-internal/querybook/compare/v0.122.2...v0.123.0) (2025-10-20)


### Features

* Add configurable sleep in presto ([#1621](https://github.com/eg-internal/querybook/issues/1621)) ([4c33785](https://github.com/eg-internal/querybook/commit/4c33785cdb11a5137493ec5620bd2b5a8b2eadf2))
* Auto generate data doc title in AI Assistant ([#1619](https://github.com/eg-internal/querybook/issues/1619)) ([db86fd6](https://github.com/eg-internal/querybook/commit/db86fd62631dd67bbc9fd538c9a7f2ff0ebd24a1))
* Merge branch 'upstream' ([702439e](https://github.com/eg-internal/querybook/commit/702439e9cdd7cd2b3958533b2c64fd55129e2e14))
* Personalized Cost Dashboard from Analytics Workbench ([#465](https://github.com/eg-internal/querybook/issues/465)) ([bdbd3b8](https://github.com/eg-internal/querybook/commit/bdbd3b8faf995506c6227cd54ea47214eb4b8ad6))
* shortcut for select next occurrence in querybook code editor ([#466](https://github.com/eg-internal/querybook/issues/466)) ([b957fd4](https://github.com/eg-internal/querybook/commit/b957fd4f255c0b5cb8e7ecde30f64d6edeaa6b9e))


### Bug Fixes

* add pagination to lists pages, fix boards from group membership on shared lists page ([#450](https://github.com/eg-internal/querybook/issues/450)) ([128eed0](https://github.com/eg-internal/querybook/commit/128eed042aa89c27ad91c9d052237e7bc747e3b6))
* disable query limit and query engine dropdowns for execute permission level ([#462](https://github.com/eg-internal/querybook/issues/462)) ([d4e7bc9](https://github.com/eg-internal/querybook/commit/d4e7bc95421179ccd9e3f9e437e679e9c828a9f9))
* Pass theme to Ava ([d9c24dd](https://github.com/eg-internal/querybook/commit/d9c24dd79247f27b0df5d38c6ca9b0b02a44bfda))

## [0.122.2](https://github.com/eg-internal/querybook/compare/v0.122.1...v0.122.2) (2025-09-23)


### Bug Fixes

* Improved Python print support for MultiIndex, NumPy arrays, etc ([521ffb6](https://github.com/eg-internal/querybook/commit/521ffb6fbe8d53498476f90ac68894940d98c248))

## [0.122.1](https://github.com/eg-internal/querybook/compare/v0.122.0...v0.122.1) (2025-09-22)


### Bug Fixes

* Fix pagination for Python cell results ([44ae7f8](https://github.com/eg-internal/querybook/commit/44ae7f862139e4a3d207a2f56808d4d54c7ba91a))
* Update StarRocks executor to enable impersonation ([ff2a71d](https://github.com/eg-internal/querybook/commit/ff2a71d2ec3748c297c0d425949b96b66787a79c))

## [0.122.0](https://github.com/eg-internal/querybook/compare/v0.121.2...v0.122.0) (2025-09-19)


### Features

* Add peer review system for queries ([52efbb0](https://github.com/eg-internal/querybook/commit/52efbb052dd3c2fc5fb93d11ac50d6dad86bc7f6))
* Add peer review system for queries ([#1535](https://github.com/eg-internal/querybook/issues/1535)) ([52efbb0](https://github.com/eg-internal/querybook/commit/52efbb052dd3c2fc5fb93d11ac50d6dad86bc7f6))
* Auto-inject DataDoc variables into Python runtime context ([#1614](https://github.com/eg-internal/querybook/issues/1614)) ([4c3d1b6](https://github.com/eg-internal/querybook/commit/4c3d1b69354487087ead6bba494f1ec1db68ea5a))
* Merge branch 'upstream-partial' into feat/upstream-merge ([74a594d](https://github.com/eg-internal/querybook/commit/74a594d03f17abff66af6051cf260e512201ee6f))
* Merge branch 'upstream' into feat/upstream-merge-2 ([839714d](https://github.com/eg-internal/querybook/commit/839714dbb3790d58307ebb397cf1dfbd5d5f6713))


### Bug Fixes

* add 1 row as default page size option for query results ([#451](https://github.com/eg-internal/querybook/issues/451)) ([51e54a3](https://github.com/eg-internal/querybook/commit/51e54a3664153b7de594b5406df2eb6977066554))
* docker image build issue ([#1613](https://github.com/eg-internal/querybook/issues/1613)) ([24af817](https://github.com/eg-internal/querybook/commit/24af817105fe1f438c0f217a6fdcdef698af9249))
* make sure the cmd-f still work on readonly docs ([#1532](https://github.com/eg-internal/querybook/issues/1532)) ([8430ef0](https://github.com/eg-internal/querybook/commit/8430ef0b974e3400140fafb935f3d120854ff4e4))
* pin Docker base image to python:3.10-bookworm ([#1612](https://github.com/eg-internal/querybook/issues/1612)) ([81795d8](https://github.com/eg-internal/querybook/commit/81795d838a9416e0c1aa084de0133eaff9421496))

## [0.121.2](https://github.com/eg-internal/querybook/compare/v0.121.1...v0.121.2) (2025-08-26)


### Bug Fixes

* execute error when accessing Board ([#448](https://github.com/eg-internal/querybook/issues/448)) ([5378894](https://github.com/eg-internal/querybook/commit/5378894ebc1aa974e0d81c407ab57766c1376ce7))

## [0.121.1](https://github.com/eg-internal/querybook/compare/v0.121.0...v0.121.1) (2025-08-19)


### Bug Fixes

* Trivial change to bump version for build ([d119dbe](https://github.com/eg-internal/querybook/commit/d119dbe2795c351ae5fcef52f222e7b8c68693d1))

## [0.121.0](https://github.com/eg-internal/querybook/compare/v0.120.0...v0.121.0) (2025-08-19)


### Features

* add execute permission level for datadocs ([#441](https://github.com/eg-internal/querybook/issues/441)) ([ebb69ca](https://github.com/eg-internal/querybook/commit/ebb69cafd79e7c410a17ae115d6a240fc44399f5))

## [0.120.0](https://github.com/eg-internal/querybook/compare/v0.119.1...v0.120.0) (2025-08-12)


### Features

* Remove JSON/CSV warnings from Trino executors, add to metastore ([8a39eee](https://github.com/eg-internal/querybook/commit/8a39eeed84b3bf216a5808c8e166f447a670f4f5))


### Bug Fixes

* Initialize warnings to empty array to force a sync ([12b527f](https://github.com/eg-internal/querybook/commit/12b527f96dcc49bfe600af7e9e85cd34426cd83d))

## [0.119.1](https://github.com/eg-internal/querybook/compare/v0.119.0...v0.119.1) (2025-07-24)


### Bug Fixes

* Update homepage links and remove Analytics Bootcamp ([de501fc](https://github.com/eg-internal/querybook/commit/de501fc169300b1d6c186df55417efb1faacac1d))

## [0.119.0](https://github.com/eg-internal/querybook/compare/v0.118.0...v0.119.0) (2025-07-18)


### Features

* Remove Collibra DIP features ([#436](https://github.com/eg-internal/querybook/issues/436)) ([63b9e42](https://github.com/eg-internal/querybook/commit/63b9e42263f9da35c128a1a83a775e6332a6191e))


### Bug Fixes

* Enable StarRocks transpilation ([90b7f90](https://github.com/eg-internal/querybook/commit/90b7f90108024b6f4b39e34fbdb4859cf68ad277))

## [0.118.0](https://github.com/eg-internal/querybook/compare/v0.117.1...v0.118.0) (2025-06-13)


### Features

* Added button to reset/invalidate github token ([#434](https://github.com/eg-internal/querybook/issues/434)) ([09306c7](https://github.com/eg-internal/querybook/commit/09306c780e8b0ff172a3d39ef254935dee5ac76e))


### Bug Fixes

* add color to tooltip title and content ([#433](https://github.com/eg-internal/querybook/issues/433)) ([d8d9ba6](https://github.com/eg-internal/querybook/commit/d8d9ba6fa8348855e2952a0f4590c3a7f447400b))
* Add DateTime option to query sample format partition filter ([#430](https://github.com/eg-internal/querybook/issues/430)) ([1b7bd77](https://github.com/eg-internal/querybook/commit/1b7bd772787f0853569aade63541fa6ff9fbd2b2))
* Optimize generating a unique name when cloning DataDocs ([c85d429](https://github.com/eg-internal/querybook/commit/c85d4294b25299182393172456e851b355203252))
* Revise StarRocks Executor Language ([bfbf712](https://github.com/eg-internal/querybook/commit/bfbf712d30b582bae6e187a1bea6b7b15e1c9594))

## [0.117.1](https://github.com/eg-internal/querybook/compare/v0.117.0...v0.117.1) (2025-04-30)


### Bug Fixes

* Add GitHub integration guide link ([596ab78](https://github.com/eg-internal/querybook/commit/596ab780fba9a45b914c1c0172c056357231c574))
* fix for csv_file_importer turning NA into NaN ([#426](https://github.com/eg-internal/querybook/issues/426)) ([50efe84](https://github.com/eg-internal/querybook/commit/50efe846627ccd2fbbf208e7a31c99c477a9eec3))
* potential fix ([#425](https://github.com/eg-internal/querybook/issues/425)) ([115bb1c](https://github.com/eg-internal/querybook/commit/115bb1c9ce531140ccb3094594c6ce838f875339))

## [0.117.0](https://github.com/eg-internal/querybook/compare/v0.116.3...v0.117.0) (2025-04-24)


### Features

* add puma generated table blurbs ([#420](https://github.com/eg-internal/querybook/issues/420)) ([7b1ec18](https://github.com/eg-internal/querybook/commit/7b1ec18a25d61e0660a6108556bfd8e426e7a0b3))


### Bug Fixes

* add table purpose to insights tab, add puma link tooltip ([#424](https://github.com/eg-internal/querybook/issues/424)) ([6c1d37d](https://github.com/eg-internal/querybook/commit/6c1d37d3c284f7af8c739cd473fe401525e778c6))
* Refactor the handeling of a failing datadoc ([10efffc](https://github.com/eg-internal/querybook/commit/10efffcf9abdf029261ed3da094a16d2afe2ebc6))

## [0.116.3](https://github.com/eg-internal/querybook/compare/v0.116.2...v0.116.3) (2025-04-07)


### Bug Fixes

* A failing datadoc cannot be disabled ([e6512cf](https://github.com/eg-internal/querybook/commit/e6512cf4f433233aad30fdf669bb3029b2bed59a))

## [0.116.2](https://github.com/eg-internal/querybook/compare/v0.116.1...v0.116.2) (2025-04-02)


### Bug Fixes

* Add query_execution_id to Trino client_tags ([#415](https://github.com/eg-internal/querybook/issues/415)) ([5e1bdd5](https://github.com/eg-internal/querybook/commit/5e1bdd5749176c6fe681f2ab82b6dd3cfef96889))

## [0.116.1](https://github.com/eg-internal/querybook/compare/v0.116.0...v0.116.1) (2025-04-02)


### Bug Fixes

* Pin openai dependency to a specific version ([8202fb8](https://github.com/eg-internal/querybook/commit/8202fb89e5145712c88fdef7992e5db94ee355f3))

## [0.116.0](https://github.com/eg-internal/querybook/compare/v0.115.0...v0.116.0) (2025-04-02)


### Features

* GitHub recursive directory listing ([900d4ee](https://github.com/eg-internal/querybook/commit/900d4ee317dd889262228c079048da0354a0fd1e))


### Bug Fixes

* Allow the sidebar to overflow if needed ([6821056](https://github.com/eg-internal/querybook/commit/682105644f45a2f0aeed056aaa7be4e9cf6d8ccb))
* Batch commits when deleting tables from a metastore ([14faa3c](https://github.com/eg-internal/querybook/commit/14faa3c0593d07610bf18fd24b8375ee53bed1a1))
* Update Confluence Links to Confluence Cloud ([#408](https://github.com/eg-internal/querybook/issues/408)) ([b24b6e2](https://github.com/eg-internal/querybook/commit/b24b6e240328456009c8bc24999b7fbdcc128e81))

## [0.115.0](https://github.com/eg-internal/querybook/compare/v0.114.0...v0.115.0) (2025-03-12)


### Features

* Connected to GitHub icon coloring ([bb3d5b9](https://github.com/eg-internal/querybook/commit/bb3d5b9690677808ad16d040da43026c2a192ace))


### Bug Fixes

* Add GHEC-specific instructions to the GitHub integration auth page ([5dbab0c](https://github.com/eg-internal/querybook/commit/5dbab0c55ef72c49e368912b961c4bbc437a7693))

## [0.114.0](https://github.com/eg-internal/querybook/compare/v0.113.2...v0.114.0) (2025-03-04)


### Features

* Enable GitHub integration ([f3be42b](https://github.com/eg-internal/querybook/commit/f3be42b2d8149529d240f9f5db3be76664d77e10))


### Bug Fixes

* automatically upload datadoc to current environment, append (1), (2), etc. if uploaded or cloned datadocs share ([#402](https://github.com/eg-internal/querybook/issues/402)) ([7a7c416](https://github.com/eg-internal/querybook/commit/7a7c4164f5781cb382d8bb6d023d81f276c243aa))
* Correctly identify egdp_analytics source data lake for EGDP env ([e6988a0](https://github.com/eg-internal/querybook/commit/e6988a0da42b459c5169cd21ccb03d3914f99b1a))

## [0.113.2](https://github.com/eg-internal/querybook/compare/v0.113.1...v0.113.2) (2025-02-26)


### Bug Fixes

* Add ref property to Ava link ([ed20cb2](https://github.com/eg-internal/querybook/commit/ed20cb2f6035d6c252a53694917679b8e24b0377))
* Query parsing error blocks execution ([5a141c0](https://github.com/eg-internal/querybook/commit/5a141c06fcbcfd99e0d7bc93b9ba5c22bde60719))

## [0.113.1](https://github.com/eg-internal/querybook/compare/v0.113.0...v0.113.1) (2025-02-25)


### Bug Fixes

* Switch AuthUser caching to Flask cache ([080bd16](https://github.com/eg-internal/querybook/commit/080bd16619d97bc8408d346f2b0e99e0ce66c4f0))

## [0.113.0](https://github.com/eg-internal/querybook/compare/v0.112.2...v0.113.0) (2025-02-24)


### Features

* Add StarRocks executor and client ([#391](https://github.com/eg-internal/querybook/issues/391)) ([5258ad4](https://github.com/eg-internal/querybook/commit/5258ad446bb7713c9b61d9ebb532bd378f7fa724))
* Batch processing for the top_tier_task ([065d3bc](https://github.com/eg-internal/querybook/commit/065d3bc24543ee727b4a15b0703ca72cda0414e8))
* Collibra criticality level changes ([bb5cbbc](https://github.com/eg-internal/querybook/commit/bb5cbbc0db58b1888af06938586c65e55fe6f2a6))
* Hidden tag support ([f44a991](https://github.com/eg-internal/querybook/commit/f44a991c2f4cba55cacdbb23dca6a3ecbb8e70be))
* remove the mysql-connector library ([1a386f5](https://github.com/eg-internal/querybook/commit/1a386f5008ce32e8b962ae91ea8422bdbf89261b))


### Bug Fixes

* added links to querybook access page for environment 404 and 403 errors ([#389](https://github.com/eg-internal/querybook/issues/389)) ([1bab625](https://github.com/eg-internal/querybook/commit/1bab625f13a40619738667e373b7d2eaa8c1017e))
* Typo in hcom_data_prod ([ced3bef](https://github.com/eg-internal/querybook/commit/ced3bef011259740784c8c849758bd69c6fcdd1d))

## [0.112.2](https://github.com/eg-internal/querybook/compare/v0.112.1...v0.112.2) (2025-02-11)


### Bug Fixes

* Boost JSON column detector priority to ensure it matches ([529fd87](https://github.com/eg-internal/querybook/commit/529fd8712ed66e493563882665a8cfa0cebaf481))
* Fix Codemirror 5 themes ([db7f23b](https://github.com/eg-internal/querybook/commit/db7f23b570b345c1290dabcc8598978db452fa14))
* Re-enable memoized user environment permissions ([48dd510](https://github.com/eg-internal/querybook/commit/48dd5108ee7c6962d45b86e8cb645f44455255bb))

## [0.112.1](https://github.com/eg-internal/querybook/compare/v0.112.0...v0.112.1) (2025-01-29)


### Bug Fixes

* Update Deprecation warning text and tag color ([53ab9cc](https://github.com/eg-internal/querybook/commit/53ab9cc643ec69281f2d206fdead9d65a271b474))

## [0.112.0](https://github.com/eg-internal/querybook/compare/v0.111.0...v0.112.0) (2025-01-28)


### Features

* Add more Platinum icons, filters, update tooltips ([9c2909e](https://github.com/eg-internal/querybook/commit/9c2909ef7b92dd1a9edc02095331dd5ae4655e3b))
* Add mysql-connector-python library for StarRocks ([8a2b3f6](https://github.com/eg-internal/querybook/commit/8a2b3f669ebd09b4cb61948c4e4eb41e0a2399e7))
* Load deprecation status into table tags, custom_info, and warnings ([#378](https://github.com/eg-internal/querybook/issues/378)) ([d4d222e](https://github.com/eg-internal/querybook/commit/d4d222e89728bf8097f8c50830ce5201768cb061))
* Update query error suggestions ([c146d99](https://github.com/eg-internal/querybook/commit/c146d99e41f2ba3fcbaed839ba87e2fbbdf1c356))


### Bug Fixes

* Update Ava message on landing page to mention sidebar ([1780d9d](https://github.com/eg-internal/querybook/commit/1780d9d7ba009d6e692336070c9aea68071d153c))

## [0.111.0](https://github.com/eg-internal/querybook/compare/v0.110.0...v0.111.0) (2025-01-24)


### Features

* Add Ava as a sidebar navigator ([54a05de](https://github.com/eg-internal/querybook/commit/54a05de4a1d922ee0973e55c9ac9a37fb9548732))


### Bug Fixes

* Change DataTableViewColumn default sort order to Default ([11c25fe](https://github.com/eg-internal/querybook/commit/11c25fe336bd63b6a1fe8f1ddad6344a1ca2bded))
* Log when sync_table deletes a table ([a2b1aa4](https://github.com/eg-internal/querybook/commit/a2b1aa4dfa91e722c192bd7199d739f20db1e3f8))
* Migrate dockerfile to Artifactory-edge ([600c2e9](https://github.com/eg-internal/querybook/commit/600c2e9d607c7d7c701e9d3adb82dfd8ba5b281f))
* Update text of Ava agent link ([3b6e752](https://github.com/eg-internal/querybook/commit/3b6e7529b1900bd1841872ac388c49e72e51df6a))

## [0.110.0](https://github.com/eg-internal/querybook/compare/v0.109.1...v0.110.0) (2025-01-13)


### Features

* Enable query vector search and SQL complete ([6c2982d](https://github.com/eg-internal/querybook/commit/6c2982d679f543394e90e21c4cae1541985316e5))
* Merge branch 'upstream' ([7f99ac6](https://github.com/eg-internal/querybook/commit/7f99ac65fbec58425800344ae2f040af36786be8))
* nlp query search ([#1531](https://github.com/eg-internal/querybook/issues/1531)) ([ac64e35](https://github.com/eg-internal/querybook/commit/ac64e35b24160917cd48eb21434a40a1fe26b968))
* Update Editor themes to work with Codemirror 6 ([fff4bdb](https://github.com/eg-internal/querybook/commit/fff4bdb338d05b20c7fcda6417d8869b95c81cbf))


### Bug Fixes

* manual schedule runs now run under current user id ([#367](https://github.com/eg-internal/querybook/issues/367)) ([06d121b](https://github.com/eg-internal/querybook/commit/06d121b88d2608b38e6334eb5e5ebf50e041af23))

## [0.109.1](https://github.com/eg-internal/querybook/compare/v0.109.0...v0.109.1) (2024-12-12)


### Bug Fixes

* Add link to Analytics Workbench chatbot ([bc944d4](https://github.com/eg-internal/querybook/commit/bc944d4b2ef72a4d3d70aac693afe492321f59c2))
* Sync Collibra links for tables via PUMA, add to the table ([18f4f4a](https://github.com/eg-internal/querybook/commit/18f4f4abc337a1aa31ca82547eeac3301ae0e0e0))

## [0.109.0](https://github.com/eg-internal/querybook/compare/v0.108.5...v0.109.0) (2024-12-11)


### Features

* Sync Platinum tag from PUMA table ([#363](https://github.com/eg-internal/querybook/issues/363)) ([0f32e61](https://github.com/eg-internal/querybook/commit/0f32e619633ab649029ec63003d539a2180fad64))
* Use error type and name to get non_retryable errors ([#358](https://github.com/eg-internal/querybook/issues/358)) ([0407218](https://github.com/eg-internal/querybook/commit/040721853cbbdddf8f757ce18e578373fe79b673))


### Bug Fixes

* Update error suggestions, add more ([f0aefde](https://github.com/eg-internal/querybook/commit/f0aefdeefa36ad6ccade3073247128edceb52511))
* Update file format mapping for table tagging ([98a245a](https://github.com/eg-internal/querybook/commit/98a245a7b7124d2724a36ac73152bddc962cf8ab))
* wrap in try except, which falls back to just fetching partition names ([#360](https://github.com/eg-internal/querybook/issues/360)) ([ceaaca9](https://github.com/eg-internal/querybook/commit/ceaaca98963213d4316267867291dd9af5705db1))

## [0.108.5](https://github.com/eg-internal/querybook/compare/v0.108.4...v0.108.5) (2024-11-15)


### Bug Fixes

* Automatically lower database/table name in HiveMetastoreClient ([35b28a3](https://github.com/eg-internal/querybook/commit/35b28a3b74b3364ffe2ec7db8b8d935179e805aa))
* Change default retry count to 1 ([a2431bb](https://github.com/eg-internal/querybook/commit/a2431bb69e07e3b28ed8e88e75798389e3fe5ba1))
* Improve error suggestion when schema does not exist ([6f93a3c](https://github.com/eg-internal/querybook/commit/6f93a3c7d9a3fa7fc44b2a1962d8371b17aaae6a))
* Sanitize_table_name() now with lowercase ([2e954d4](https://github.com/eg-internal/querybook/commit/2e954d4aea6a3b76008f5494ece02af060b38741))

## [0.108.4](https://github.com/eg-internal/querybook/compare/v0.108.3...v0.108.4) (2024-11-04)


### Bug Fixes

* Remove latest tag ([5c457f9](https://github.com/eg-internal/querybook/commit/5c457f99ae8da91b2bf414fd746a1696b8c14f65))

## [0.108.3](https://github.com/eg-internal/querybook/compare/v0.108.2...v0.108.3) (2024-11-04)


### Bug Fixes

* Remove unused docker tags ([515d5fa](https://github.com/eg-internal/querybook/commit/515d5fa0171a95225b5b6330f3effe69dd637c96))

## [0.108.2](https://github.com/eg-internal/querybook/compare/v0.108.1...v0.108.2) (2024-11-04)


### Bug Fixes

* Catch exceptions during delete_schema/table_not_in_metastore ([76a8ff0](https://github.com/eg-internal/querybook/commit/76a8ff08013e3f54c296ba353501c424e0a639fe))

## [0.108.1](https://github.com/eg-internal/querybook/compare/v0.108.0...v0.108.1) (2024-10-25)


### Bug Fixes

* Restrict non-retry-able errors for initial release ([96864cc](https://github.com/eg-internal/querybook/commit/96864ccd322bd6fe1a9d216ae4b6a29137ea14d9))

## [0.108.0](https://github.com/eg-internal/querybook/compare/v0.107.0...v0.108.0) (2024-10-25)


### Features

* include query retry count in Trino client tags ([28f4531](https://github.com/eg-internal/querybook/commit/28f4531a482ad4821b6cd5e2283f33cfc427d5d0))


### Bug Fixes

* Revert "fix: Upgrade celery to 5.5.0rc1" ([0f07d9c](https://github.com/eg-internal/querybook/commit/0f07d9c4fbc91d8f650dd5cad0ca60378872e050))

## [0.107.0](https://github.com/eg-internal/querybook/compare/v0.106.0...v0.107.0) (2024-10-22)


### Features

* Abort scheduled retries for timed out queries ([#340](https://github.com/eg-internal/querybook/issues/340)) ([dedecbc](https://github.com/eg-internal/querybook/commit/dedecbc65e54223f3cc9e9d7ce74f0693916471e))
* Explicitly set `worker_cancel_long_running_tasks_on_connection_loss` to False ([3418da5](https://github.com/eg-internal/querybook/commit/3418da5e4fd8c8105a149baf314edce849308d5b))
* Stats logging of all QueryExecution status counts ([3d8acdc](https://github.com/eg-internal/querybook/commit/3d8acdc4f1620f2a9cf797933c5de44d3279d09d))


### Bug Fixes

* Upgrade celery to 5.5.0rc1 ([18d9685](https://github.com/eg-internal/querybook/commit/18d9685cfcd1c6ce449bb98bcb87bc3f770b9baa))

## [0.106.0](https://github.com/eg-internal/querybook/compare/v0.105.0...v0.106.0) (2024-10-16)


### Features

* Stats logging of the number of queries with INITIALIZED status ([6162c40](https://github.com/eg-internal/querybook/commit/6162c40e2e03c1277e0b617daf976f576bab6c6d))


### Bug Fixes

* Catch exceptions during celery stats logger ([79a9358](https://github.com/eg-internal/querybook/commit/79a935839bd6bc70c406a1c1f5f071eb2cd61120))

## [0.105.0](https://github.com/eg-internal/querybook/compare/v0.104.2...v0.105.0) (2024-10-09)


### Features

* Add query editor themes in User Settings ([#329](https://github.com/eg-internal/querybook/issues/329)) ([b3990a6](https://github.com/eg-internal/querybook/commit/b3990a6cffe84da77e96dcd3f1a5a3c5677fa8af))
* Improve metastore sync reliability ([05d4a1f](https://github.com/eg-internal/querybook/commit/05d4a1f31ad97dd48520fb779789444568205fe6))
* modify retry options for scheduled datadocs ([12ebcfb](https://github.com/eg-internal/querybook/commit/12ebcfb8b461514dbc6221a5607e9e62d64ec2cb))
* rename the current Top Tier feature to Trending and change icon to a flame ([#333](https://github.com/eg-internal/querybook/issues/333)) ([b8cd958](https://github.com/eg-internal/querybook/commit/b8cd958dc1efadc9cf405143dfbca3fdc7afe6c0))

## [0.104.2](https://github.com/eg-internal/querybook/compare/v0.104.1...v0.104.2) (2024-09-30)


### Bug Fixes

* Allow restricting query_execution search to recent IDs only ([109a71f](https://github.com/eg-internal/querybook/commit/109a71f75919370e2fe7a2ea3153de83440aa3fd))

## [0.104.1](https://github.com/eg-internal/querybook/compare/v0.104.0...v0.104.1) (2024-09-25)


### Bug Fixes

* Add additional error suggestions ([8aeb744](https://github.com/eg-internal/querybook/commit/8aeb744d12bc9fc04ea746022831b476b9978a80))
* Fix `egdp_dwh_` prefix mapping ([d6a5c8c](https://github.com/eg-internal/querybook/commit/d6a5c8c37c4067937cf8df4500357f7a8a0066c2))

## [0.104.0](https://github.com/eg-internal/querybook/compare/v0.103.0...v0.104.0) (2024-09-24)


### Features

* Add an error suggestion for "already executed" error message ([0d1470f](https://github.com/eg-internal/querybook/commit/0d1470f3f177a4ca5107fc6813b47ace00921ce5))


### Bug Fixes

* Remove backend/broker logs since they contain credentials ([c4aa614](https://github.com/eg-internal/querybook/commit/c4aa61477f07bc5438db93530c294115ac4b0afe))

## [0.103.0](https://github.com/eg-internal/querybook/compare/v0.102.2...v0.103.0) (2024-09-24)


### Features

* Add option for CELERY_MAX_TASKS_PER_CHILD ([e2de1c4](https://github.com/eg-internal/querybook/commit/e2de1c47390841476955f5f2bc71649845f3589d))
* Enable Celery task compression (gzip) ([d5603e6](https://github.com/eg-internal/querybook/commit/d5603e639e10192b864a4b30491a6d746c439d5d))


### Bug Fixes

* redirect the Change Logs and FAQs in the Help section to internal pages ([#319](https://github.com/eg-internal/querybook/issues/319)) ([86df2df](https://github.com/eg-internal/querybook/commit/86df2df12791766d30b72ee7c1cefa231c717213))
* useLoader shows previous error messages if data is already loaded ([3631313](https://github.com/eg-internal/querybook/commit/36313131e8445e580f5d3cc6b5c11a2922a04d7a))

## [0.102.2](https://github.com/eg-internal/querybook/compare/v0.102.1...v0.102.2) (2024-09-19)


### Bug Fixes

* Fix docker image tagging ([d8a7863](https://github.com/eg-internal/querybook/commit/d8a7863d648b180cc34d387c093202bb213d2b38))

## [0.102.1](https://github.com/eg-internal/querybook/compare/v0.102.0...v0.102.1) (2024-09-18)


### Bug Fixes

* Disable Elasticsearch Geo IP Downloader ([dffa634](https://github.com/eg-internal/querybook/commit/dffa6341acb0d3b8c5522b315c78b7c824dbf8f8))
* Enable redis_socket_keepalive ([a508165](https://github.com/eg-internal/querybook/commit/a508165624674146b356e8ccc7cc2402c4db0d37))
* Fix ORC file format ([48d0843](https://github.com/eg-internal/querybook/commit/48d084388b268111967e011191926581c8b8fa8f))
* modify scheduled filter in datadoc search to only show datadocs that are both scheduled & enabled ([#311](https://github.com/eg-internal/querybook/issues/311)) ([3cfc1b1](https://github.com/eg-internal/querybook/commit/3cfc1b18a73b72b4be7507b10925a30fe9405ead))
* Remove top tier table cache ([353d15c](https://github.com/eg-internal/querybook/commit/353d15cfb1cca3618b7957deda3cce1aab648944))

## [0.102.0](https://github.com/eg-internal/querybook/compare/v0.101.5...v0.102.0) (2024-09-10)


### Features

* Remove XLSX export option from UI ([96a5850](https://github.com/eg-internal/querybook/commit/96a5850572604256f3091bfbe3587d7645d305e1))
* Revert "fix: Upgrade celery to 5.5.0b1 to address Redis issues" ([d8a504b](https://github.com/eg-internal/querybook/commit/d8a504bc9360f418c5b7255cc2b83523ba41d026))

## [0.101.5](https://github.com/eg-internal/querybook/compare/0.101.4...v0.101.5) (2024-09-05)


### Bug Fixes

* Turn Celery heartbeat back on ([6dc435d](https://github.com/eg-internal/querybook/commit/6dc435dbef61645dc7827188061b00578ef77380))

### [0.101.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.101.3...0.101.4) (2024-08-26)


### Bug Fixes

* Add updated_at to indexed queries ([07ffd3c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/07ffd3c3ab25116720133dd8fb8f34b226f7023b))
* Optionally ingest sample queries to vector index ([982f65d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/982f65d0ffb21a80b349c888c87f0806b9fdd8b2))

### [0.101.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.101.2...0.101.3) (2024-08-26)


### Bug Fixes

* Track popularity and add filter to the ingest_vector_index task ([428315c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/428315c34e93d5b4e5d5f49cd63cfeda02a7723d))

### [0.101.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.101.1...0.101.2) (2024-08-23)


### Bug Fixes

* Fix ingest_vector_index infinite loop ([c947499](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c94749915f44ac99a8e2a23e262a110eb0b9eaa6))

### [0.101.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.101.0...0.101.1) (2024-08-22)


### Bug Fixes

* Fixes for top tier calculations ([5f767be](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5f767bee6c80f1e34b5456f051360eb11b2da81c))

## [0.101.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.100.0...0.101.0) (2024-08-22)


### Features

* some tab animation options (#289) ([cd25553](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cd2555338fae091cd65baebb2f70846be01100d5))


### Bug Fixes

* Update `ingest_vector_index` tasks, add top_tier kwarg ([9c66b2b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9c66b2b3c88368d56dd45055a960d18073d321ae))
* XLSX is now created the same way as the CSV, so it will always have the same number of rows. (#294) ([d0a9ae2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d0a9ae2c6d81b8e0180380d4a3b4b97476c7831f))

## [0.100.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.99.0...0.100.0) (2024-08-18)


### Features

* Improve AI Assistant prompts ([95fb9b6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/95fb9b66d5cf4836b39a148c7eeaf8a795c75dc4))
* Sync Querybook admin task ([05418ac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/05418ac7b1f903300e43cbd2e7d5a19e7652c3e7))


### Bug Fixes

* Fix table search tags overflowing container ([ca49dcd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ca49dcd6bb87882203254a22c352d306b3491ee4))

## [0.99.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.98.4...0.99.0) (2024-08-09)


### Features

* Improve partition view ([933a3d4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/933a3d499fe2d90ecb3e8231f08f247f2e8f5b81))
* Load table boost_score via PUMA / top tier ([9c00b49](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9c00b494c2bb9543727351713883bc96ecca547c))
* Only load partitions for top tier tables ([9dffedf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9dffedf804dd6e890f5b118ccd8c5c2d887731f5))
* Rework table tag sync, include rank & icons ([08d2251](https://github.expedia.biz/eg-analytics-platform/querybook/commit/08d2251bd650a03da5e0db3ae3fcb78b1976914f))


### Bug Fixes

* Add metastore loader logging for schema count ([d0d565c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d0d565c676496f8b526634d63896c762c4631568))
* Break word on survey question ([26be5d8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/26be5d8f94f1b1a295a58850878578669d9b4b63))
* Case-insensitive exact match ([5024188](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5024188624a86409364f4c083821ff5d8ab0c4e0))
* Don't show empty partition lists ([16924ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/16924ec64dc19d8f7da47a46baba0269990703f3))
* Limit loaded partitions to 5 earliest/latest ([6512141](https://github.expedia.biz/eg-analytics-platform/querybook/commit/65121413f9bf426b21b8573f477cf85279ee027d))
* Upgrade celery to 5.5.0b1 to address Redis issues ([f0037ea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f0037eaee9e88bab3480a771917fcc6151b13644))

### [0.98.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.98.3...0.98.4) (2024-08-08)


### Bug Fixes

* Fix session closed errors due to top tier changes ([c9c41df](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c9c41dfbc235cc04ffd9bc328b3b01c3f76a9afd))

### [0.98.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.98.2...0.98.3) (2024-07-25)


### Bug Fixes

* Add top-tier icon in search results list ([9171190](https://github.expedia.biz/eg-analytics-platform/querybook/commit/917119018c14f269a6b2d23e34f88a9f419f752d))
* Add top-tier icons and popover details about PUMA ([a9a9e43](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a9a9e431cbf7f93da65b056fb40a3bc308c04e7f))
* Change to `egdp_test_analytics` source data lake ([4f620a6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4f620a6be6ff5e38846b7a209ba933a262413944))
* Fix missing column sensitivity tag for nested values ([b0aa7b1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b0aa7b1c211b2e5c02de385e81770f440367faa1))

### [0.98.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.98.1...0.98.2) (2024-07-23)


### Bug Fixes

* Handle tables with `eg-sensitivity.is-sensitive: false` ([c0486da](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c0486dafdd5337c8b8f93bc03cff9c66598c7e9f))

### [0.98.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.98.0...0.98.1) (2024-07-22)


### Bug Fixes

* Table search sort by relevance by default ([9ce4389](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9ce4389c81c1b6d23bb8be203496dbe61ad82bcb))

## [0.98.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.97.0...0.98.0) (2024-07-22)


### Features

* Add `eg-source-control-url` properties to Table Links ([526dcf8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/526dcf830fc6568c45a0586756039856525b3a97))


### Bug Fixes

* Change default AI model, add context sizes for new models ([52204ee](https://github.expedia.biz/eg-analytics-platform/querybook/commit/52204ee84661a7ce9c9f366cf34e33dfec9a4a33))
* Handle source data lake for egdp-waggledance ([69e76cf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/69e76cff749e7239f905ef8150c973cb09670fd7))

## [0.97.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.96.0...0.97.0) (2024-07-19)


### Features

* Sync Top Tier tables via PUMA data ([96579ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/96579ec154b2a6a2ca72303183fd8d401aeb09b7))

## [0.96.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.95.2...0.96.0) (2024-07-10)


### Features

* Add `DATABASE_ECHO` to enable debug SQL logging ([3a4405b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3a4405b31e63ee7315b01748a7139aaf99d2463e))


### Bug Fixes

* hide pin button for adhoc queries, but keep for datadoc queries (#268) ([ba81988](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ba819887071d2dd6d7aae7a126f14987981a9d87))
* Metastore sync tables with a single transaction ([8e867ea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8e867eaa4f6aebbbca294ddbec8a5e6cd8c39369))

### [0.95.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.95.1...0.95.2) (2024-06-28)


### Bug Fixes

* Revert automatic limit in backend, restore old behavior ([4587449](https://github.expedia.biz/eg-analytics-platform/querybook/commit/45874494483265752f13eab13ef37a4e7a604cc1))
* Un-reverts "feat: added warning at top of doc and at each cell with select statement and no limit (#160)"" ([d35d0d4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d35d0d4b622a8db4b0427d7c0b602e4bba4218c6))

### [0.95.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.95.0...0.95.1) (2024-06-28)


### Bug Fixes

* Add limit transform support for `LIMIT ALL` ([1883c32](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1883c323347e86ce61dcbd9a13c8748cac4be847))
* Catch transform errors in `has_query_contains_unlimited_select` ([58e2186](https://github.expedia.biz/eg-analytics-platform/querybook/commit/58e218621ea61edef27982ff27ca4715b0b98195))
* Send language to query transform when running DataDoc ([0a0e2c6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0a0e2c61af2fed7f9879d70abbec6d13c0a359f6))

## [0.95.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.94.1...0.95.0) (2024-06-25)


### Features

* Revert "feat: added warning at top of doc and at each cell with select statement and no limit (#160)" ([aa78920](https://github.expedia.biz/eg-analytics-platform/querybook/commit/aa78920645d45b9be97b63a744e5b23e70a41048))

### [0.94.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.94.0...0.94.1) (2024-06-25)


### Bug Fixes

* Remove missing parser/sqlglot.txt, already required ([a09ddc2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a09ddc23c63915c6f7cb237e28ba722631795b24))

## [0.94.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.93.0...0.94.0) (2024-06-24)


### Features

* Apply row limit transform to query in backend (#263) ([dc139cb](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dc139cbb159c1880c139f950eafbca45df264f1f))
* Table Search by Owner ([d33bf53](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d33bf53954817e115fa2b30c1a9b6f25b4e80c11))

## [0.93.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.92.0...0.93.0) (2024-06-18)


### Features

* add [@mention](https://github.expedia.biz/mention) to select a table for the command input (#1432) ([067d96d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/067d96db321e1f2f2908dece1e4ee5a9470a31e4))
* Add any links associated with a table to querybook descriptions (#1450) ([d81d582](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d81d5824b381b24a4d45884ab5da3a37361ff0d7))
* add table sampling support (#1421) ([4287294](https://github.expedia.biz/eg-analytics-platform/querybook/commit/428729492e9834f2d0ffac82eed2324d779a1711))
* Auto-load built-in notifiers if configured (#1420) ([8c6600c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8c6600c84221ffedd3d7469ef0c6e78e8cde2c85))
* Improve Cron schedule support (#1395) ([26007d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/26007d6b7ca2678003c7cf4fb45dce2e2218c1be))
* update text2sql ui (#1429) ([a6f73fc](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a6f73fc0829a181f7b73c6106c9a734a18ad3277))


### Bug Fixes

* add back text2sql survey (#1452) ([b8d9a95](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b8d9a95e0636421459d50da44c73a176a5e50c63))
* add csp header for iframe embedding (#1442) ([80a9eee](https://github.expedia.biz/eg-analytics-platform/querybook/commit/80a9eee94b1b70e339379fe1558981279dd72400))
* add default search parameters for table concise search (#1439) ([302b6ac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/302b6ac7ae86e63ca980713eed8b87e472bb2020))
* add warning to notification, bold text (#262) ([0897413](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0897413cb1d6e5ca633c81089bcfb49002f92383))
* added sort key when more data tables are loaded in a search (#239) (#1424) ([174e444](https://github.expedia.biz/eg-analytics-platform/querybook/commit/174e4448a2cef8e2f285f4f21fee236a7450dbfa))
* Correct mapping for table_updated_at/table_updated_by (#1426) ([44d8055](https://github.expedia.biz/eg-analytics-platform/querybook/commit/44d8055ff71e8a808280a1627a13fa5632d42e6d))
* enable websocket cors for production (#1425) ([3e992ee](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3e992eea99411a75aeb6eb41fe60100b0e6afb59))
* Fix Email notifications to multiple email addresses (#1437) ([2dbc30d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2dbc30de9f7340e463e62269987392e8c2fe6b5b))
* Fix upstream merge issues ([b5f29b5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b5f29b5b5693fb41a0cbb72e43cf4f675d674e18))
* Metastore ACL support for wildcard prefix match (#1423) ([1e664d3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1e664d305a5c6057de02864f9322ed1a3c929617))
* move slack channel to top of table description (#1446) ([af818be](https://github.expedia.biz/eg-analytics-platform/querybook/commit/af818be536469ecdddc1c26ef0a12b2bef088e1b))
* move to first match on search term change (#1416) ([3507385](https://github.expedia.biz/eg-analytics-platform/querybook/commit/35073850d0d7e5d522eac761f37197bbbd09d211))
* move workflow link to source query tab (#1445) ([74790d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/74790d6c99f2a8a2653fe628ee59bb76afb6501c))
* querybook edit access issue (#1444) ([29fdf95](https://github.expedia.biz/eg-analytics-platform/querybook/commit/29fdf95bde7d635042c956fc951677e38b23704f))
* requirements/dev.txt to reduce vulnerabilities (#1427) ([357132a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/357132ac9de392b500b75f37b81919f0657e30e3))
* revert to use searchConcise for mentioning a table (#1438) ([4c74ac8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4c74ac8ce0d1489b5e3f4a98cc4cb9bc70bd8dd4))
* update cookie config (#1431) ([b445a22](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b445a2272cb965f7a5deb6f022de0772245913ec))
* use match_phrase_prefix on full_name field for table suggestion (#1433) ([cd11be9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cd11be939e6955341de701228cd0d6d52e944ed5))

## [0.92.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.91.1...0.92.0) (2024-05-17)


### Features

* Added button to import a datadoc from a JSON file (#258) ([4f6eaba](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4f6eabafd5a6bb97e7c197dc2800eb6469a60941))
* Added download button to convert datadoc to JSON and download it (#257) ([f32af60](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f32af6062e7f0bfd36a1857f2b36e39eefe31889))
* Improvements to the Landing page ([7765999](https://github.expedia.biz/eg-analytics-platform/querybook/commit/776599929b5e7f7fa8260367cdd90bad1f3dbdad))


### Bug Fixes

* link users directly to the querybook access page ([2985a8e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2985a8e76938841f3af9fff568dc1723f5dc7049))
* Use `read_csv()` for XLSX export to ensure entire file is read ([a272785](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a2727855eebcba27a8da21f4407d254a55cd55c7))

### [0.91.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.91.0...0.91.1) (2024-04-25)


### Bug Fixes

* Add openpyxl for Excel exports ([6f07114](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6f071141e0e7095d8340e3f1bdb26571ff1ddc7e))
* Implement read_raw for S3 result store ([0767555](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0767555bd7a7215f7b1f2dbbaddbe68202233162))

## [0.91.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.90.4...0.91.0) (2024-04-19)


### Features

* Add current_user variable and slugify filter to Jinja ([632ea66](https://github.expedia.biz/eg-analytics-platform/querybook/commit/632ea66fa740c302f92924d615a1ed5cd0e99f16))
* add download as xlsx option via streaming (#254) ([bca3c28](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bca3c2807ea0e4459a06095a9ecfd8bfd5684378))


### Bug Fixes

* Make datadog optional and switch to lazy importing ([f146764](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f146764bcaaadb61234264623a1f56b9b8bc6856))

### [0.90.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.90.3...0.90.4) (2024-04-11)


### Bug Fixes

* Add additional file formats ([60764d2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/60764d259d46d0304515bf32863fd8a1272a0a91))
* add bom to downloaded csv (#251) ([4d2ccd6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4d2ccd6bcebf4ef005f167d5cb3433d4f20c2dad))
* Fix Email notifications to multiple email addresses ([4ef3acd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4ef3acd2f0f145733742c840f2dbda87fb2070cd))

### [0.90.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.90.2...0.90.3) (2024-03-25)


### Bug Fixes

* Improve file type detection for EgHMSMetastoreLoader ([c1c9e87](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c1c9e876f32c34fc184a3966677d5fe0114bc40c))

### [0.90.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.90.1...0.90.2) (2024-03-18)


### Bug Fixes

* Fix int bug in EG Hive Metastore ([67d2eb4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/67d2eb43368f10d0e3cb06a940bc6d6ff2d309e7))

### [0.90.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.90.0...0.90.1) (2024-03-15)


### Bug Fixes

* Pin openai dependency to avoid httpx issue ([02fa2a6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/02fa2a6f52e1925a5728f6d39db503cca57035be))

## [0.90.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.89.0...0.90.0) (2024-03-15)


### Features

* Add a warning to Avro tables with external schema files ([12327b8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/12327b83971794f251f7e22983b7a48733a35d62))
* added data_cell_id and data_cell_title to trino tags (#238) ([dd7b6d0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd7b6d0d29d423f73fc6a32b2f7623f9a09b7d33))
* Clone DataDocs into other Environments ([ffb6602](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ffb66023bb657f41e9b1d625fd67de3ac41f3851))
* Detect table file format ([791d7f1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/791d7f1464d76d6da4d4dc5fd201b46de858ba92))
* enable impression logging of survey events (#1411) ([34cb6d3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/34cb6d342d8513e46075efa0914850a2ed0d4b39))
* Improve metastore sync for views ([a42bad3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a42bad3217b1d6172da1d7e91c19159579745edc))
* Staggered refresh for Hive Metastore ([dd19c32](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd19c320990a156d8ea8095334478f6a830768a9))
* upgrade langchain version (#1406) ([7208c05](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7208c05aba1ae04c80be1f6e86170a5a9d73b7e7))


### Bug Fixes

* add support for a sum column analyzer (#1418) ([e313560](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e313560cfe9e7d45766766616c247254f94969c6))
* added sort key when more data tables are loaded in a search (#239) ([888a409](https://github.expedia.biz/eg-analytics-platform/querybook/commit/888a40916646f851050516f5c486f6e977a18f83))
* Fix create task schedule task_type (#1408) ([4e1c721](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4e1c72186f894f151d66871260dd16db5c9e8920))
* Fix DataDoc cell move down button (#1410) ([dd185bf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd185bfb0a42b067c54b5caa5fd6f6a619d33681))
* Fix table_updated_at ([976b539](https://github.expedia.biz/eg-analytics-platform/querybook/commit/976b53941074cbd3ce10ec1d58e9236bdc2cd055))
* Improve Partner Data tagging ([957e626](https://github.expedia.biz/eg-analytics-platform/querybook/commit/957e6264e48d5f78f48c5ca1346d9011bc7c0b56))
* Langchain-upgrade related changes ([7206c21](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7206c2149cd2ef8e967e19ea8cef26a3a4b74574))
* Metastore ACL support for wildcard prefix match ([aad82b1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/aad82b16138155441061ab7dff3d8ca9ae54cb24))
* requirements/base.txt to reduce vulnerabilities (#1394) ([8190652](https://github.expedia.biz/eg-analytics-platform/querybook/commit/81906520cf7f967622e013835ca082cd3a75a5b3))
* schema filtering in table search modal (#1348) ([4d41106](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4d41106157bfdaf50bd201877688e259eb0884da))
* Support serialized JSON environment variables (#1415) ([c3be536](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c3be536f286629be20c493f6b0e9d99f3b48e6c2))
* survey for table modal is blinking (#1396) ([6ddda71](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6ddda718439364d0b21743738a257f721246dc82))
* Update `unique_table_ownership` constraint to allow owner per type (#1403) ([8531df1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8531df1dbbfcb630af89f568db291f7ee729c25b))
* Update text highlight color for dark mode ([37cb8e1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/37cb8e1d66f9885cec2b76389d3be56fb1ed9921))
* XSS injection with Querybook RichTextEditor (#1412) ([bc620da](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bc620dabaaf13ff1dcb30af0b46a490403fb9908))

## [0.89.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.88.0...0.89.0) (2024-02-28)


### Features

* updated table upload messages ([f37fb15](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f37fb151b0a48ccf6f02715a8564e7d4ab533e4b))


### Bug Fixes

* pre-commit prettier (#233) ([ea117ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ea117ec68bb8fa411a4df0e2c583773ceb190f24))

## [0.88.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.87.0...0.88.0) (2024-02-23)


### Features

* Support `default-partition-spec` on Iceberg tables ([66f7032](https://github.expedia.biz/eg-analytics-platform/querybook/commit/66f7032a744d2e19afd14d7125c1a39a02d011d8))


### Bug Fixes

* Support serialized JSON environment variables ([8da7e30](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8da7e302b886d93b7deadc333b7678e4222ffdba))
* update disabler task with kwargs (#230) ([4c764f8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4c764f89ae3914cc4aaf9a44011d0b94480821bf))

## [0.87.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.86.2...0.87.0) (2024-02-19)


### Features

* Add local embedding configurations ([00378fa](https://github.expedia.biz/eg-analytics-platform/querybook/commit/00378fa8778445870f46573388b1d9b934d4b5f8))
* Add Ollama AI Assistant ([cd4df1e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cd4df1e20b2ef83fd0a209c1151d705d955019ef))
* Add rate-limiting patch for `create_and_store_document()` ([713ffac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/713ffacc4a65e79824d450cb4864a5cee6d703e3))
* Elasticsearch 8 vector store implementation ([4ea0357](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4ea0357827302b16fa82e2129419c9371409a001))
* Store `updated_at` field in vector store ([75bb23e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/75bb23e33db71200cd98110e7bcbf2569418997e))
* Task to ingest tables into vector store ([d6af0a4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d6af0a4565567e3ba87bd8f997d9525fe4478202))
* Text embeddings configuration for GenAI Proxy ([c5f4171](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c5f4171b06c7ef3a2fda7e5eac335a0703d8768c))


### Bug Fixes

* added check for is_group is null so that older users can be assigned as owners (#228) ([37e0523](https://github.expedia.biz/eg-analytics-platform/querybook/commit/37e05235e0fefa39f643841608916a82de723e95))
* Fix create task schedule task_type ([3efc54f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3efc54f6bb1bd1ac26df2e0594d4b758352d429d))
* Fix DataDoc cell move down button ([9773d0d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9773d0d8b69d882d834615ac08b81afa6f9ea61a))
* Fix langchain dependencies ([c5ddf7d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c5ddf7d16cef4f03a47bf8aefe1a275c73a4d479))
* Improve suggestions for user names in Elasticsearch ([e70c473](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e70c47306b51c10fe627e4f6d3afdf47b6781e48))
* Shorten table tags automatically to fit within the database limit ([314bdb4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/314bdb42ebe8280715b4d5ca2365003d550b8a04))
* Update `unique_table_ownership` constraint to allow owner per type ([315249b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/315249be9f4b486fdbfa5246cd2d9a9517262ee2))
* Update tracking URLs to use `info_uri` field ([8cf1450](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8cf1450c53b805c38f33db50947bc8ba3f01c3ec))

### [0.86.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.86.1...0.86.2) (2024-01-26)


### Bug Fixes

* add a clear_sheet parameter for google sheet exporter (#1401) ([0e1917c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0e1917cb591582cd8fd261679ad44e40fe9bb015))
* modify trigger for query_authoring survey (#1400) ([8c87e3e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8c87e3e98a8bf6c0cb4e658b66d78acadcdefe4f))
* Update metastore error message suggestion ([33e140e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/33e140e079db9dcb4d9ace92c1e36bc532368917))

### [0.86.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.86.0...0.86.1) (2024-01-25)


### Bug Fixes

* bump for new build ([c014cea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c014cea83578b7b6ff90a6dd6e2b8c39af7373c8))

## [0.86.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.85.0...0.86.0) (2024-01-24)


### Features

* Support for Azure OpenAI Models ([b4a2dfe](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b4a2dfe8c69c8bb553b33e02ea3113f3869d2ace))


### Bug Fixes

* Add a 100-char field limit for column metadata in the slim prompt ([dd83bc0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd83bc061affbe93f50fc0283ad1885a9ecec9cf))
* Trino linting improvements ([68c29ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/68c29ec1662115a07e660ec1f0231145a522bdf6))

## [0.85.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.84.0...0.85.0) (2024-01-19)


### Features

* ask users to confirm tables before query generation (#1339) ([becf905](https://github.expedia.biz/eg-analytics-platform/querybook/commit/becf905db483ae446ea3b972326988e28b673cc4))
* Enable and configure Surveys ([c277ede](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c277edeca132790826d41725a04ad5ab881c4d14))
* fixed up clean_up_archived_data_doc and added the option to pass in -1 for run_all_db_clean_up_jobs (#1387) ([900d2d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/900d2d671e4b358954587db0a7b6e509c5198183))
* refactor ai-assistant plugin and add vector search support (#1325) ([f3ce910](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f3ce9100a2b761628bb17a9b147d71f87c929872))
* update column stats ui, add sort by usage to columns (#1389) ([370948f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/370948f8e3bd9476637d00e0cf4e4121bc27ef8c))


### Bug Fixes

* Add scroll bar to Query Engine Status popover (#1353) ([f8d8dd4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f8d8dd439af0018ba528c8435d3c280d1841ef04))
* cast table max upload size to int (#1374) ([e2efe8e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e2efe8e2764759854f158a2703c6d3f8932bdb4a))
* Fix DataDoc contents overflow in non-Chrome browsers (#1332) ([18c86a6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/18c86a6010fbc9d4fa8e708f8ca3343718915a6a))
* Fix URL joining in TrinoConnectionChecker2 ([b63b691](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b63b691932447a29abc66d0b06372e4a2103b17f))
* possible unauthenticated SQL injection when login (#1383) ([7214963](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7214963fef91098b28d9a0306fb3440015a0f32f))
* randomized default schedule time (#209) ([7534222](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7534222b3048aef588d76089c04ae44621f568a0))
* Refactor AI Assistant to support non-streaming mode ([91d0942](https://github.expedia.biz/eg-analytics-platform/querybook/commit/91d094231239b49b84f4d5c99fb45150a2881afc))
* replaced 'does not exist' errors with custom error message (#210) ([3f1e0ad](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3f1e0adff007b6d6685c6cd617ad3c34c174a2d8))
* s3 table upload location (#1376) ([0b5699a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0b5699a111da452be762f55e2844dc74f400a48d))
* some small changes and fixes for AI assistant (#1333) ([21c3fd4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/21c3fd4aa75ef7437792fa735fbdce3641620333))
* Store group description in `public_info` (#1384) ([3686d0d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3686d0ddc4ae5fe590cb8f6b6a3a099afd104f19))
* store the task type value rather than enum when creating a task (#1329) ([9f8c001](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9f8c0017cdad555255dc7a3a99e392b44262f722))
* Update runservice worker scripts to disable unneeded features (#1371) ([09ffc40](https://github.expedia.biz/eg-analytics-platform/querybook/commit/09ffc408176c15ebcbca7267820c92152a156a71))


### Reverts

* Revert "fix: Fix DataDoc contents overflow in non-Chrome browsers (#1332)" (#1336) ([5d0ed1d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d0ed1de375f162a995f614685101e89a1d6500e))

## [0.84.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.83.2...0.84.0) (2024-01-12)


### Features

* Create an updated TrinoConnectionChecker2 with HMS and Ranger ([bb7b6f0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bb7b6f00afba3b70715ae3e66fd28a25736675b2))
* Cron schedule support ([0464f29](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0464f295a7006bdfc19bccc93c53bc3521272594))


### Bug Fixes

* added [inherited] to board permissions ([903dd4b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/903dd4b82274ad777a8d673d62f27684d3bdb79f))
* Url Links transformer open in a new tab ([14cfbf7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/14cfbf730d79da5d529e8c7681aab2816a380dcd))

### [0.83.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.83.1...0.83.2) (2024-01-05)


### Bug Fixes

* Don't unfurl nested groups in sync_ldap_group ([5979368](https://github.expedia.biz/eg-analytics-platform/querybook/commit/59793687a1b481e485d1597e54f84feeaaa650fd))

### [0.83.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.83.0...0.83.1) (2024-01-04)


### Bug Fixes

* fixed inherited permissions not converting to proper read/write values (#200) ([064664e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/064664ec8eb80d537c375beb59070b4454eb3125))

## [0.83.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.82.2...0.83.0) (2024-01-03)


### Features

* Added user group permissions for lists and datadocs (#137) ([48ba132](https://github.expedia.biz/eg-analytics-platform/querybook/commit/48ba132ad4cfb53867466021aaff21acca129e7a))
* fixed up clean_up_archived_data_doc and added the option to pass in -1 for run_all_db_clean_up_jobs ([fb1aa32](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fb1aa32cf4253728243469cdcafc41d7f8cffb91))
* Sync LDAP Groups task, syncs group membership from LDAP ([c5007e0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c5007e009265bba659a11e17d459c03fa5600673))


### Bug Fixes

* fixed active_tasks only displaying 1 tasks per worker (#198) ([ab5f2be](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ab5f2be533785e21c28816dae8d26ff13a6ff863))

### [0.82.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.82.1...0.82.2) (2023-12-14)


### Bug Fixes

* remove all unicode characters, leading and trailing whitespace, and newlines and return characters (#196) ([2eabab8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2eabab807686d2bda46f9191417d4ddcce9fea38))

### [0.82.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.82.0...0.82.1) (2023-12-13)


### Bug Fixes

* fixed active_workers monitor ([5258f25](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5258f255179c2e2b7dd7a7493b5e9216ed9ad054))

## [0.82.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.81.0...0.82.0) (2023-12-12)


### Features

* added datadoc id and title to trino tags (#191) ([4e97e86](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4e97e86d91fe29becfe9a9403a238d0487d7f7c4))


### Bug Fixes

* Move Datadog container to a separate profile ([685943d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/685943dc36a6dd3ecf5e77c8a2381905b00401a0))
* Rewrite clean_up_stuck_task_run_records to remove subquery ([c0cb7ba](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c0cb7ba68228a45e42f3a87224190cf259b2b5c3))

## [0.81.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.80.0...0.81.0) (2023-12-08)


### Features

* reset permissions to 'read only' and disable schedule on datadoc ownership change (#181) ([15f6f11](https://github.expedia.biz/eg-analytics-platform/querybook/commit/15f6f113aa60e21e5c1feb1522d4754645e84f78))

## [0.80.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.79.2...0.80.0) (2023-12-06)


### Features

* Data Dog Monitoring for Querybook (#179) ([f54f3a8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f54f3a86766077697831d15da2adbc0db57a62a5))


### Bug Fixes

* Update disabled datadoc cell styling ([97e8622](https://github.expedia.biz/eg-analytics-platform/querybook/commit/97e86224379124510659eb445b1e2c0bcb70b14f))

### [0.79.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.79.1...0.79.2) (2023-11-28)


### Bug Fixes

* moved ai tool tip to right position (#187) ([06750ea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/06750eab1c85a264875298441d3fad710563e651))

### [0.79.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.79.0...0.79.1) (2023-11-22)


### Bug Fixes

* Fix clean_up_stuck_task_run_records ([1627957](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1627957290caa9868eea1868844c0daf09129de7))
* Update clean_up_stuck_task_run_records to use on_datadoc_completion ([de9dbae](https://github.expedia.biz/eg-analytics-platform/querybook/commit/de9dbaebbf6e137e19d57cd66d523852c990dfec))

## [0.79.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.78.1...0.79.0) (2023-11-20)


### Features

* Update clean_up_query_execution_task to cancel stuck Schedules ([9cd8d43](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9cd8d43bcd9ffcf03038d90fd97a1291bd7e1e5d))

### [0.78.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.78.0...0.78.1) (2023-11-17)


### Bug Fixes

* eval table max size, basic table upload log ([c39a66b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c39a66b4a36543ce8ea41df8f52502cb1944dc5e))
* eval unsafe, log fixed ([8169bba](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8169bba1406b7ab0eb4b1ed5ad06936a315ce93e))
* Move upload logs to base_exporter, add row limit ([8386f4d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8386f4d00db2628e1b7856d8fce374d868d59c32))

## [0.78.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.77.1...0.78.0) (2023-11-14)


### Features

* Auto-create user accounts for Metastore-syncs table owners ([7be9d61](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7be9d61468672b7fd891d0310323e1e32fa74da0))
* Improve EG's metastore sync with owners, tags ([b87e190](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b87e190525623a6c9054102a6d4eb3cc444297bb))

### [0.77.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.77.0...0.77.1) (2023-10-24)


### Bug Fixes

* Remove DataDoc container query to fix z-index problems ([f65e4aa](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f65e4aa5e25a3ebfd65356b53bb6b0aa13c4e97b))

## [0.77.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.76.4...0.77.0) (2023-10-23)


### Features

* Load managed database credentials ([d60bfa4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d60bfa4afbb21785913b0abe883f9260d78d05a6))


### Bug Fixes

* Add scroll bar to Query Engine Status popover ([2e64017](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2e64017345368627ea8be5c3ff4bcc4f492f6f3f))
* Change prod_worker's celery log level to INFO (from default WARN) ([581f3ca](https://github.expedia.biz/eg-analytics-platform/querybook/commit/581f3ca3b076d6b0923cd8510e23e343c853b972))
* GenerateSample not displaying fixed (#177) ([2fdd587](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2fdd587b83014dca2cc2e0c22dd3d99afc7e43be))

### [0.76.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.76.3...0.76.4) (2023-10-09)


### Bug Fixes

* change column descriptions to readonly=false and write_back (#174) ([5766659](https://github.expedia.biz/eg-analytics-platform/querybook/commit/57666595f81919691f82b67192ecb4a670c98c3e))

### [0.76.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.76.2...0.76.3) (2023-10-04)


### Bug Fixes

* fixed bug where datadoc page would go blank if template blocks were used in query cells (#172) ([0211d24](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0211d240a85e499318d0f1ee5790fe539dd6ffdf))
* Update worker startup script ([2f3b206](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2f3b2064048f331421288d6104cbf11a5c5f4e50))

### [0.76.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.76.1...0.76.2) (2023-09-28)


### Bug Fixes

* Fix optional Trino client tagging ([3ed0b30](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3ed0b30d71b02718ad6dcd90a3c5c5c9e174a975))

### [0.76.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.76.0...0.76.1) (2023-09-28)


### Bug Fixes

* Add OpenAINoStreamAssistant to workaround GenAI Proxy limitation ([d79ff69](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d79ff692fcc58bc03eed76cc428a7821590a8018))
* removing old code from merge issue (#169) ([0c5d737](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0c5d73756487cf35e40880775c8be5c4e10a8252))

## [0.76.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.75.0...0.76.0) (2023-09-27)


### Features

* added warning at top of doc and at each cell with select statement and no limit (#160) ([68f44de](https://github.expedia.biz/eg-analytics-platform/querybook/commit/68f44ded926f214ab72d21015061bd7fa622e8f0))


### Bug Fixes

* Always show data elements in table filters ([7f3fd14](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7f3fd14305135f2582e322d0d834347da685e283))

## [0.75.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.74.0...0.75.0) (2023-09-26)


### Features

* Add index on query_execution.status column ([bac411f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bac411f0b09e46f571914eba9fbcc2bb07e4ce37))


### Bug Fixes

* Container query to wrap DataDoc cell header at small sizes ([2cae969](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2cae969bac1ffd794527436e49068daaf370843c))
* Revisit disabled DataDoc cells, fix cell title scrunch ([31d7049](https://github.expedia.biz/eg-analytics-platform/querybook/commit/31d7049c2790906f64d6b26f144a2f381aa0a349))

## [0.74.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.73.1...0.74.0) (2023-09-22)


### Features

* Disable clean_up_query_execution on worker start, move to task ([4783c30](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4783c300f3084fed6c16c31f1e9b2fe63f226bc3))

### [0.73.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.73.0...0.73.1) (2023-09-21)


### Bug Fixes

* Fix lazy-loaded DataDoc cells ([856b4be](https://github.expedia.biz/eg-analytics-platform/querybook/commit/856b4be7747a3e0845a1f1bd93e851a03bdd6a6c))

## [0.73.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.72.2...0.73.0) (2023-09-21)


### Features

* Add query execution id and execution type to trino query tags (#161) ([620d02b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/620d02bc1ff6e6f5eb5e296ac70937b6ea73cf08))
* Disable Prevent Overlapping Runs by default for new schedules ([184cb52](https://github.expedia.biz/eg-analytics-platform/querybook/commit/184cb52f06c1e3ec54e501468237eff21d656084))


### Bug Fixes

* Fix DataDoc contents overflow in non-Chrome browsers ([9e09128](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9e091280119f4a7008866fea5780092789be5ea7))
* Initialize environment variables from Vault ([56a5e25](https://github.expedia.biz/eg-analytics-platform/querybook/commit/56a5e25fa1cd201cb8fda3d16d06bbb91a41099e))
* Revert "feat: Add additional config file" ([7e9558b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7e9558b77ef941c14675ce586e0abb0f1dc8dcb7))

### [0.72.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.72.1...0.72.2) (2023-09-14)


### Bug Fixes

* Load OPENAI_API_KEY/BASE from config to environment variable ([0573e10](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0573e1000d47d85e54a1bc8a9e4f2590121a6c2f))

### [0.72.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.72.0...0.72.1) (2023-09-14)


### Bug Fixes

* added new format list to display show create results on separate lines (#157) ([60ad49b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/60ad49b0d8261a170a729fa3bb5b16f4bd61d7ab))

## [0.72.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.71.3...0.72.0) (2023-09-13)


### Features

* added sensitivity tags in metadata sync ([a277b3d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a277b3d306003725d83479a6c3ae479407cac04c))
* Enable and configure AI Assistant ([50ad6a1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/50ad6a131e07eef41a00a9f2f88ab8dca0f00069))
* load table warnings from metastore (#1317) ([b39d358](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b39d35811a96c961091d5a6836514355bb3e3601))


### Bug Fixes

* Allow Metastore tag sync and user-managed tags ([5850aff](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5850afff22ba70c83e24f5c2f2b836f7f55a4d98))
* Board Ownership Transfer did not reassign owner (#1299) ([47ca744](https://github.expedia.biz/eg-analytics-platform/querybook/commit/47ca7448cda2bc197dd722f457582e453677935d))
* Case-insensitive tagging and expanded list of data elements ([e2f0ecd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e2f0ecd4abaa1a6a53e90b5120c412f95e025828))
* fix warning displaying on wrong table (#1307) ([21ea259](https://github.expedia.biz/eg-analytics-platform/querybook/commit/21ea2594e431113cf597a66d66bea8030c779db7))
* init_es.py script not completing due to TypeError (#1309) ([2625209](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2625209d700c1e887b6e0e2eefac8d2658a42947))
* Migrate to new Nodesource repository (#1318) ([f770e80](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f770e807fe43d8f98a7e0ea8bd62980842ecaad7))
* UI Tutorial 8-11 now focuses on page components (#148) (#1310) ([416f48a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/416f48a0e3b2f6d3437cdd523f7194c72ca01043))

### [0.71.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.71.2...0.71.3) (2023-08-31)


### Bug Fixes

* Add Analytics Bootcamp's Querybook 101 link ([e48e7a4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e48e7a46491b4942915152fec69da8ef8977f498))

### [0.71.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.71.1...0.71.2) (2023-08-31)


### Bug Fixes

* Specify Trino tracking URL ([b4e9539](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b4e9539c205fb6ae3cf8a2b80aa25d1b9652954a))

### [0.71.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.71.0...0.71.1) (2023-08-30)


### Bug Fixes

* Migrate to new Nodesource repository ([a209479](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a209479886f4fdc29ab788541549668a3187b157))

## [0.71.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.70.1...0.71.0) (2023-08-30)


### Features

* added ability to select number of default rows displayed in query results for adhoc queries and datadoc queries ([86bbce5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/86bbce54450bd1a3d09d235b302285c911385949))

### [0.70.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.70.0...0.70.1) (2023-08-17)


### Bug Fixes

* Add missing import for TrinoUserError on eg_trino_client ([23bc92d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/23bc92d4b125470c6a54a6a22d1cc8ecda3a87d6))

## [0.70.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.69.2...0.70.0) (2023-08-11)


### Features

* Add analytics ([7a29760](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7a2976096bf34a313003c6717a0001fc82378811))
* add context logging for AI features (#1277) ([803ae8b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/803ae8ba2ec86fd03b5cd01efb273317c30807d6))
* add error handling and use EventSource for AI assistant (#1265) ([4d7bb1b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4d7bb1bb89cedda49db5212a53e3fdb54f41f991))
* add LLM powered text2sql support (#1276) ([8659fb7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8659fb7f3cf9af76a4dff3f08a01fc41c5fcdf21))
* add query auto fix in AI assistant (#1270) ([6c9b809](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6c9b809ffaa4227c30c9927a86af41209c30b491))
* adopt data element in text2sql prompt (#1301) ([4cec5c1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4cec5c16bd1a6b60c6459c530ec9f637c1bd8670))
* data cell + table comments (#1279) ([ccb032c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ccb032cdc97997befdd966ddd3e809236f73a594))
* Generate query title by using LLM (#1255) ([467e581](https://github.expedia.biz/eg-analytics-platform/querybook/commit/467e58118f7265cc15813212fa4d8508d19d4ad2))
* Injectable Secrets into the Helm Chart (#1260) ([d7a7ff0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d7a7ff0ae34aca9962feafdc97e355b0555dd62d))
* pass proxy user to sqlalchemy executor (#1303) ([18e15b7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/18e15b7bc4eec88fa5541d30525dc4766be83e25))
* tune table search ranking (#1248) ([1d50874](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1d50874a3877f55b18c77a0cc22a88c6ffff7438))


### Bug Fixes

* add post processing to ai generated content (#1291) ([148d96b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/148d96b67367a62a6dbbc5de195e80366baaa3b2))
* delta stream  parser (#1280) ([b4da637](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b4da637d22ec127bd3407818403947afa4f0cc5e))
* fix warning displaying on wrong table (#146) ([a76c981](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a76c981bcbed52c514fc6d033c1b3f3a425e5801))
* getting .y from a null value (#1256) ([2c5520a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2c5520a2a9108ad0bdf8aace0877293e55e7c039))
* IO Exception on closed file (#1237) ([dada0e9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dada0e9c530687e92934c78588bbbcaf6ec8fc80))
* only handle the query generation keydown event when not streaming (#1287) ([9eb197f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9eb197f4f3fb4ef9f2bd0050bfbcd3672191af1c))
* query title disappears when opening a datadoc (#1286) ([32baf49](https://github.expedia.biz/eg-analytics-platform/querybook/commit/32baf49af5ae0026dbcad4919ffe59ae54f8bcbf))
* some small changes of ai assistant (#1290) ([3f61155](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3f61155818c304c0d464414784df4aeb177fdb50))
* UI Tutorial 8-11 now focuses on page components (#148) ([5d67175](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d67175bfd270180b1d48cc0f7051dba5acb93c2))
* undefined result from stream parser (#1281) ([1424995](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1424995e589606100d00d69b68b7b51e8e48e9f3))
* Update EG custom transpiler functions (#145) ([bd52ac7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bd52ac755e1a0272932cbe8c5081aa5d93a2a95d))

### [0.69.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.69.1...0.69.2) (2023-08-01)


### Bug Fixes

* replace hadoop table owner with e4b-bedrock when schema starts with eps_prod (#143) ([2199ad0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2199ad0a0264699a0aed9ee8f994d54d3b2967dc))
* Update Landing Page documentation links ([140dbd1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/140dbd1a48a7754f7f4511308266ab7ac8dcc0e6))

### [0.69.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.69.0...0.69.1) (2023-07-24)


### Bug Fixes

* fixed transfer of board ownership not working (#141) ([772e3e3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/772e3e3e20f626cc46e276ef3aab5a1c82d3aba6))

## [0.69.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.68.1...0.69.0) (2023-07-12)


### Features

* Added button to execute all query cells in a datadoc after the current cell (#139) ([898b854](https://github.expedia.biz/eg-analytics-platform/querybook/commit/898b8543fa2b17345791c1fff279bcb01e4350ec))


### Bug Fixes

* **deps:** Update sqlglot version (#140) ([f0ec788](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f0ec788fda046cfbde971fd3eb80e2a01fd872b8))
* Specify python version to fix npm issue ([3ac25b4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3ac25b40494eec272e99721ba61fff94ffc55c2a))

### [0.68.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.68.0...0.68.1) (2023-05-26)


### Bug Fixes

* Add `Exceeded CPU limit of 10.00d` error message ([32f5381](https://github.expedia.biz/eg-analytics-platform/querybook/commit/32f5381def282817a98c435f642c2daeca45249c))
* Fix incorrectly merged upstream changes re: run_datadoc.py ([48bfb27](https://github.expedia.biz/eg-analytics-platform/querybook/commit/48bfb27f46a4023acdb8e76dfdc02022770678e6))

## [0.68.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.67.0...0.68.0) (2023-05-25)


### Features

* add button to sort columns in view table UI (#1187) ([c14babb](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c14babb8727ef876c3263b51c8dc2b5bcc787906))
* add configurable timeout to querybook (#1207) ([4e234d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4e234d6d4bbb2a2b174d7d7712fd9c1bbbb06bfb))
* add data element on the sidebar, show descriptions (#1233) ([0e79d74](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0e79d74a4ade776a462ceb5e664807f0e905fa30))
* add data elements to demo (#1232) ([8b8fcc9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8b8fcc92c355a35b64beec473217fa0c703ff8e3))
* add data elements to ES index (#1213) ([3759cf7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3759cf7e9336575c3eafc0abcd485c785794721b))
* add descriptive error msgs (#1150) ([8ab460f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8ab460f038c09caeafc3cbcd1267ac05ac980655))
* add more metadata support (#1182) ([2bc6052](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2bc605282c9e6f0385934d034022a38f96ae5c58))
* add new metadata type - data element (#1191) ([2742cdc](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2742cdca0e22cf3f864b84b4195f37eb95a2f1c6))
* add stats logging (#1204) ([354b08d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/354b08d3c4846076dd09725624d8700647b5e8bf))
* Added 'Scheduled' filter for datadoc search and clock icon (#131) ([6a156cd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6a156cdb96b7e14d8c3ca3523895e78999e10c5d))
* create data element along with syncing table (#1193) ([0113ba3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0113ba39795f3e2b86c7836c22d03b60073ea7c5))
* display data element description as column description (#1195) ([7ec024b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7ec024b15d9bc0f2c1ec3f5d357871d89ba331d6))
* find the closed color in ColorPalette (#1184) ([5ec6a4d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5ec6a4da8cc77b3c9afeb17bf1033d2e5bfca6a2))
* make datadoc table of contents sidebar resizable (#1218) ([e95927b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e95927b2861081988f10d9cba0aa1b33ab35f746))
* make struct form fields ordered (#1181) ([4a7c8da](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4a7c8da3a430643a77db0fa441a2a4913ae80ae8))
* update some stats metrics names and add tags (#1208) ([8ca4322](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8ca4322891920104b95db3ab5cf0e497ee53df61))


### Bug Fixes

* add get_schema_location to metastore loader (#1214) ([6500610](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6500610e9995de34cb609a7dd43f347f6502e916))
* add tooltip length (#1192) ([25b1895](https://github.expedia.biz/eg-analytics-platform/querybook/commit/25b189501ff834503110cc64c883614b95e154a7))
* check nullish of table property value (#1197) ([c500823](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c500823f7ad74519fe939e46592080801b60bdfc))
* column name overlaps with type (#1203) ([dc7ceaf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dc7ceafe6714c11b972179c80b2156b81c4ef977))
* docs_website/package.json & docs_website/yarn.lock to reduce vulnerabilities (#1143) ([423410d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/423410db85af8cf75fad5c1ce2301fc8e66e39c4))
* dup table description in table search (#1216) ([fa35faa](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fa35faa231341f5f47b0fb706ae85a430fea7731))
* Enable mssql transpiling (#1178) ([d89187d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d89187d4cee35de67d77c537d9823f3f64bad875))
* Ensure meta_info is updated when an exception occurs (#1230) ([d902232](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d90223231e7e7bd37d9125f879e495be6bc91558))
* EntitySelect (#1215) ([c141948](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c141948cf4088a9b4d14d8e487a5ba668fd8582a))
* find nearest color (#1185) ([65eb774](https://github.expedia.biz/eg-analytics-platform/querybook/commit/65eb7749caca66cc81ed515273991c93ddfec9b9))
* make entity select creatble be false by default (#1227) ([8a3a775](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8a3a7758a40b781b37aba9e5cc8d17abd9064b6c))
* metastoreId can be ill defined (#1235) ([06cd2f9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/06cd2f90791a8b72b47c42377b514320d5a2bcba))
* remove broadcast from socketio.emit (#1202) ([cf96f9a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cf96f9ab3205b3a75340f633d817f9fe3dd50377))
* remove decr stats logging events (#1223) ([92d507d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/92d507d3f812eee1619edfb0cd10a7a3c282fddc))
* Remove postgres requirement from base to fix automated test build ([7a74e57](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7a74e57eb906ca5cc55489115ab93f10065493b0))
* requirements/base.txt to reduce vulnerabilities (#1167) ([fb1b4e5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fb1b4e59c35f98c4b042c77cd0a75cad14c434b4))
* requirements/base.txt to reduce vulnerabilities (#1205) ([f59f4ca](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f59f4cac366e4682ffddc74d1dbfe12daa24bfd2))
* skip empty query cells when run datadoc (#1217) ([c508f2b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c508f2b178365cfbce8dad5f7b76409369e84626))
* some bug fix related to tag and data element (#1199) ([2bb8873](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2bb887356a234920d83e1018bdf47c4d54062d68))
* title format check for Snyk (#1219) ([d3aa06a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d3aa06a2764a4f33b560707c7e3a8332265eccde))
* update data_element table charset to utf8 (#1209) ([5994a9d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5994a9d9b461d2dbfdd9fb9daca03b574f348e03))
* Update error suggestions ([fcb56c2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fcb56c2d1079a90cdad5fa192541ececab494fd7))

## [0.67.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.66.0...0.67.0) (2023-05-04)


### Features

* Added feature that can disable/enable datadoc cells to exclude/include them from run all or schedule runs (#128) ([defe9a3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/defe9a3e25c8561753536d2b6ae27b4d5e6d4cd5))
* Added Note about file size limit in table upload window (#129) ([9f00c10](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9f00c104f31f5f4e5131f8d180fb0cfd1efb8c1f))

## [0.66.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.65.0...0.66.0) (2023-04-25)


### Features

* Added key icon for partition keys in 'View Table' window (#126) ([7f62f6d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7f62f6d1a2b02e8577b88cfe8712f9b17cc90e2b))
* Added key icon for partition keys in table hover window (#125) ([a648b83](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a648b835bfb75b3e2af4ede4a53d29517eb56cec))


### Bug Fixes

* Add Postgres driver to requirements ([aa92f61](https://github.expedia.biz/eg-analytics-platform/querybook/commit/aa92f61d2da658ab83e155256b3a11a3e9866d58))

## [0.65.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.64.3...0.65.0) (2023-04-20)


### Features

* Added a marker to denote when a variable will be deleted in a datadoc (#124) ([0e469a6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0e469a6b432d6d9b6e8753caf2d0a964481c387a))
* Added ability to add a datadoc to a list that is shared with th… (#122) ([2b7b40e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2b7b40e60a796c6b3acfe14f2370c37c3aa722af))


### Bug Fixes

* Ensure meta_info is updated when an exception occurs ([2a1622b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2a1622b1493c24129eb205e958830da3c324424d))

### [0.64.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.64.2...0.64.3) (2023-04-12)


### Bug Fixes

* Disable Celery heartbeat/gossip/mingle features to fix reconnect errors ([c28f252](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c28f25234d9a46312d44f1af0079c729471972fa))
* Fixed issue where shared lists page tries to fetch inaccessible boards and added public lists with write access to shared list page (#121) ([b2e490e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b2e490e97afa24eb0a5e16253f759f8a7272486e))

### [0.64.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.64.1...0.64.2) (2023-04-04)


### Bug Fixes

* Prevent overlapping runs should be optional ([42e548a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/42e548a072940b39480d5c0370d7131829dc8fc8))

### [0.64.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.64.0...0.64.1) (2023-03-28)


### Bug Fixes

* Remove <p> </p> tag from email notification subject line (#117) ([4d15647](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4d156476358c352e43ed5c315de22791dfadebce))

## [0.64.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.6...0.64.0) (2023-03-27)


### Features

* Added All Shared Lists page (#116) ([de1ffb5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/de1ffb514596be45775d5d920eaa5bfb01bd513d))

### [0.63.6](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.5...0.63.6) (2023-03-22)


### Bug Fixes

* Notifications removing underscore and pound sign resolved with jinja2 escape filter (#115) ([162ddac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/162ddacc5b4c57c108828bfbf582bff3f9d72368))

### [0.63.5](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.4...0.63.5) (2023-03-21)


### Bug Fixes

* remove broadcast from socketio.emit (#1202) ([958cfb6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/958cfb65016864d4795c44cc61b80ccf902e63f9))

### [0.63.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.3...0.63.4) (2023-03-21)


### Bug Fixes

* Fix lint errors related to Schedules ([74278de](https://github.expedia.biz/eg-analytics-platform/querybook/commit/74278de90818cd1e6b3be951695f124e0cd30287))
* Remove unused function to fix build error ([4d24499](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4d2449961e23682b96a7dfd56a11166136bf925a))

### [0.63.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.2...0.63.3) (2023-03-21)


### Bug Fixes

* LIMIT ALL can now be used in Querybook (#112) ([ad8fe0a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ad8fe0a6bd40fae0ce4451cd8cb33a759e3f1a9d))

### [0.63.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.1...0.63.2) (2023-03-16)


### Bug Fixes

* Extend DataTableColumn type length to 32768 ([0fadd6e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0fadd6e6eeb2d7524c55c89de4d5c7feb3d99343))
* Truncate long types in DataTableColumnCard ([65094aa](https://github.expedia.biz/eg-analytics-platform/querybook/commit/65094aa121312b24e794a7aeba28fe63b4c3abcc))

### [0.63.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.63.0...0.63.1) (2023-03-09)


### Bug Fixes

* Fix replace option for table upload ([293d109](https://github.expedia.biz/eg-analytics-platform/querybook/commit/293d10909cf579316e8abc14a7abfde059c3cc41))

## [0.63.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.6...0.63.0) (2023-03-08)


### Features

* Patch PyHive to support TLS connections ([782ff72](https://github.expedia.biz/eg-analytics-platform/querybook/commit/782ff72b078c5083e3904e1436f9cb5ed961b3e6))

### [0.62.6](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.5...0.62.6) (2023-03-08)


### Bug Fixes

* mismatched scheduled run times (#106) ([0936f0e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0936f0ea79090baa504568d6ddf982edc9cd818a))

### [0.62.5](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.4...0.62.5) (2023-03-08)


### Bug Fixes

* adjust ui max width (#109) ([88f5a64](https://github.expedia.biz/eg-analytics-platform/querybook/commit/88f5a644712bd5c3a1ae014b62173ce645f7271c))

### [0.62.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.3...0.62.4) (2023-03-07)


### Bug Fixes

* add more retry delay options in minutes (#107) ([c95d860](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c95d8607e2e05e2250ad8669fcff806455150e0a))

### [0.62.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.2...0.62.3) (2023-03-03)


### Bug Fixes

* reset last_run_at on reenabled schedule (#105) ([111764c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/111764c0ab2a956364ed1c8f2ab4de10fe019f64))

### [0.62.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.1...0.62.2) (2023-03-03)


### Bug Fixes

* jdbc update regex (#103) ([a495f32](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a495f32542223babcfa113b3d54bb9836f0c1c50))

### [0.62.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.62.0...0.62.1) (2023-03-03)


### Bug Fixes

* change default step to 1 cron parsing (#104) ([a164635](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a16463510ce98a369eec40379427a801c9461973))

## [0.62.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.61.2...0.62.0) (2023-03-02)


### Features

* disable run doc if doc is already running (#101) ([fceadbd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fceadbda9f08bd869370dddc39aea4691e2a0845))

### [0.61.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.61.1...0.61.2) (2023-03-02)


### Bug Fixes

* update regex (#102) ([b55912e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b55912e9b04fa0781691ec4949d25883bb60e50a))

### [0.61.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.61.0...0.61.1) (2023-02-28)


### Bug Fixes

* Ignore deleted metastores in Table Upload ([44be8a7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/44be8a777b1de2bd38f1a072c094d6efbe8286a7))

## [0.61.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.60.2...0.61.0) (2023-02-24)


### Features

* add button to sort columns in view table UI (#99) ([c0ca76a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c0ca76a0446aa4a90ba850f3f0165d696e55ee7d))

### [0.60.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.60.1...0.60.2) (2023-02-24)


### Bug Fixes

* Enable mssql transpiling ([fae1675](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fae1675dba0fbc08cf13b21ce381de79aa94b254))

### [0.60.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.60.0...0.60.1) (2023-02-24)


### Bug Fixes

* Merge branch 'upstream' ([db9ef13](https://github.expedia.biz/eg-analytics-platform/querybook/commit/db9ef138b390fc1c6a4aaf1253bfdc6147d28623))

## [0.60.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.59.1...0.60.0) (2023-02-24)


### Features

* Improve Slack notifications ([f29f3b4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f29f3b4381b0f32b25c7d250cd9196c9722f0d35))

### [0.59.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.59.0...0.59.1) (2023-02-23)


### Bug Fixes

* update runtime exec and jdbc missing err msgs (#97) ([577f736](https://github.expedia.biz/eg-analytics-platform/querybook/commit/577f7360599688253b4c07bc589792a05556887c))

## [0.59.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.58.1...0.59.0) (2023-02-23)


### Features

* update delete cell confirmation popup (#95) ([67eaea4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/67eaea43011d6caf7a28fc544fbb67db7c33379c))

### [0.58.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.58.0...0.58.1) (2023-02-20)


### Bug Fixes

* update runs at language (#94) ([c6a31d1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c6a31d1b2de892266a1fc5d5e627f500f7bf51c3))

## [0.58.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.57.0...0.58.0) (2023-02-20)


### Features

* Add ability to cancel dead queries (#1159) ([51be7c6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/51be7c6e531622c600da2b09e2b4af8cbf8b76b8))
* add estimated time for query execution (#1158) ([7a25679](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7a256797ffdbe6c2ba60376fd0f864c96fa236c5))
* add message when linter failed to run (#1157) ([dd35c4e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd35c4e580dce947d9949d254295df6a7728e97e))
* add user group db schema support (#1144) ([4734e01](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4734e01295e1d734bda42d5554f3e8f7fbb9416a))
* support for a general validation message in query editor (#1156) ([f3cff53](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f3cff53ef97c4a901e260fec1ed92190a4bcc37d))
* toggle run all notifications (#1162) ([53a70e1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/53a70e11ce35d44cdd16ce0ec0ec3b9495c1091d))


### Bug Fixes

* event logger when current user is None (#1153) ([bb96eaf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bb96eaf5fb34aa17a91598106fc00172e3cd7883))
* filter null store values (#1163) ([5abedbe](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5abedbe3f90fc1c01b382a8e5af093641320d498))
* number type variable with value 0 (#1154) ([15f084f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/15f084f0a9481b57352ae78ee6093765d5114f09))
* sql-formatter (#1152) ([efdbd7b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/efdbd7b6ea8d7c84802b37c4bcdbcc12e4f78e95))
* unify status code and move user error to 400 (#1161) ([118a8f5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/118a8f59de13511b6f804223a6427ebd6288c22e))


### Reverts

* Revert "feat: add estimated time for query execution (#1158)" (#1166) ([1f54e67](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1f54e6782017a5abeb5c17cf449c23cd667268e0))

## [0.57.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.56.0...0.57.0) (2023-02-17)


### Features

* add ability to choose other hourly options (#93) ([dbe40a3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dbe40a33569012ee2f1f480d42e6240b7dadf47e))

## [0.56.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.55.0...0.56.0) (2023-02-17)


### Features

* Sync new user permissions on login for env/query engines (#92) ([58598b8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/58598b8608e4d6ccad735fe3a2413f577b346525))

## [0.55.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.54.1...0.55.0) (2023-02-13)


### Features

* toggle run all notifications (#91) ([823dc01](https://github.expedia.biz/eg-analytics-platform/querybook/commit/823dc01b5dbfd4033bce58f46b49bd1dc12fd64a))


### Bug Fixes

* filter null store values (#90) ([25616ae](https://github.expedia.biz/eg-analytics-platform/querybook/commit/25616ae6d19de684886d5885685bc68f3aa88143))

### [0.54.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.54.0...0.54.1) (2023-02-08)


### Bug Fixes

* only get error msg if exec error ([7dbb8d4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7dbb8d4aeaa05cfaa2ea1b8b5573826b411aeb99))

## [0.54.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.53.1...0.54.0) (2023-02-08)


### Features

* add metastore loader config (#1134) ([d0c0270](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d0c0270d26c1e5aaf61b248f52280322805234ee))
* add search box to hide columns popup (#1128) ([0e050e8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0e050e8c163001925b1119713f498bce10f165bf))
* add status and board filters for scheds page (#1076) ([772471b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/772471bcdb99c7a86ed138db0b3d9ab2a4a140c6))
* query engine search scroll (#1136) ([b663b04](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b663b047103e866e475d6702ffcb07301ee97457))


### Bug Fixes

* add safe suppress to sqlformat error (#1141) ([0b85af3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0b85af33a5e8707d5cce138b0e6b6653df25c14f))
* Fix Scheduled DataDocs Only toggle (#1149) ([8ab38b3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8ab38b3dcf94ee84cf75b017992917d8d0736a1d))
* rich text editor crashes on clicking in readonly mode (#1148) ([7217403](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7217403c936a91f7c099c929f4a3489606c62f9c))
* stay on current env after deleting doc (#1138) ([07a8b62](https://github.expedia.biz/eg-analytics-platform/querybook/commit/07a8b626f2dc034a5b96300a102210d5a3a34afa))

### [0.53.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.53.0...0.53.1) (2023-02-08)


### Bug Fixes

* refactor method to get descriptive error msg ([a002e93](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a002e93615e0e96b6b4160c75b3c061bc7980c83))

## [0.53.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.52.2...0.53.0) (2023-02-07)


### Features

* add descriptive error msg run all datadoc ([d4b66b6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d4b66b65f86ad814796f29d02937753126ac2d97))

### [0.52.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.52.1...0.52.2) (2023-01-30)


### Bug Fixes

* stay on current env after deleting doc (#86) ([5228d12](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5228d12cb310d7409712382279f62ebc53f5f476))

### [0.52.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.52.0...0.52.1) (2023-01-27)


### Bug Fixes

* Removed hardcoded endpoint from transpiler ([18c2981](https://github.expedia.biz/eg-analytics-platform/querybook/commit/18c298121be17849ff316cab821a239f773a93fc))

## [0.52.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.51.0...0.52.0) (2023-01-26)


### Features

* query engine search scroll (#79) ([a37946a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a37946aedca869882a283344761bddac9ee1181f))

## [0.51.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.50.4...0.51.0) (2023-01-26)


### Features

* add clear button to hide columns search bar (#81) ([c5082ff](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c5082ffa13f1d7df484dd029d7f408a30b7642f1))

### [0.50.4](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.50.3...0.50.4) (2023-01-25)


### Bug Fixes

* axios error display (#1133) ([ba6d738](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ba6d73804594a5210e42cf0be3ec4f8664f59165))
* react-table version (#1132) ([9e55937](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9e5593791e5f680a71093ddfb0bd5855a9e8430e))
* remove timeout for presto explain (#1135) ([6f003ab](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6f003abdc1736497a3763af5bd381ddf7ffb8839))

### [0.50.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.50.2...0.50.3) (2023-01-25)


### Bug Fixes

* External File Issue Fix and Refactoring (#80) ([8c399ca](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8c399ca0db2feb9593c2d1ec46c76bc87ab94075))

### [0.50.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.50.1...0.50.2) (2023-01-20)


### Bug Fixes

* Extend error suggestion regex for SHOW CREATE TABLE from Adhoc ([541bb56](https://github.expedia.biz/eg-analytics-platform/querybook/commit/541bb56bdc067fbe5b303298e84a081531bb614e))

### [0.50.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.50.0...0.50.1) (2023-01-19)


### Bug Fixes

* json-bigint hasOwnProperty undefined issue (#1129) ([7cdb1db](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7cdb1dbd652cfcabdac5ed0b824548b374ab6889))
* update /event_log api path (#1130) ([2962b58](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2962b587bdee1e0e88b03bfb6fc7a421130f411e))

## [0.50.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.49.0...0.50.0) (2023-01-18)


### Features

* add search box to hide columns popup (#76) ([e2ccc27](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e2ccc27f44bf85d771fbdfe5aad342dbe99f841a))

## [0.49.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.48.0...0.49.0) (2023-01-17)


### Features

* a bunch of small ui fixes and improvements (#1114) ([0033314](https://github.expedia.biz/eg-analytics-platform/querybook/commit/003331485824bd6b503346890049674600d22f88))
* add drag and drop for templated variables (#1112) ([24652a3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/24652a38260f4b68c114f0aed2f22bdca67853aa))
* add frontend context logging (#1115) ([6a951f8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6a951f874013e9e949d27106acafb021b0273856))
* add logout event hook (#1104) ([1527ff3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1527ff3e83799bf6b95d87718e13bae75b22df9d))
* Add shortcut for toggle ToC, update datadoc short cuts (#1107) ([6bbbc8f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6bbbc8fbca44141afae2166d3af7f15accdb9887))
* add support of running all cells of a data doc (#1102) ([b80b48c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b80b48c6d13fc763d723bd91c9466d1fbac170c6))
* add websocket logging (#1110) ([b6eec5a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b6eec5a99618cd5ea20a7f66274e85509c7569c5))
* auto add quotes for table/columns (#1109) ([d2c1f09](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d2c1f09218e62993fdc53c5e87d70e9b97eb35f4))
* Make exact table search result auto show up (#1106) ([d543644](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d543644af31618b301a0919556051d20a636628d))
* Merge branch 'upstream' ([386cc89](https://github.expedia.biz/eg-analytics-platform/querybook/commit/386cc89d92dae7820b137899df772d25b9ee64e4))
* validation now works for templated query (#1119) ([155baca](https://github.expedia.biz/eg-analytics-platform/querybook/commit/155bacac23bec71ba0b5fafadd66724fd021092a))
* Visualize complex Hive column types (#1091) ([05de0ca](https://github.expedia.biz/eg-analytics-platform/querybook/commit/05de0ca35b108789a25d2c5803ba2a5e93a5ba53))


### Bug Fixes

* Add disabled indicators to Schedules list (#1122) ([d059a7a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d059a7a0c98e1c2d46debae92b160595a91a3f13))
* Chart date axis bug (#1108) ([d1633c0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d1633c0fd5e8ce5f1a9ecb66a844f46373aa007b))
* Extend DataTableColumn type column length (#1121) ([e80a92a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e80a92ad52673020ac8f8069e6a0b7e4dac1d067))
* hasOwnProperty is not a function issue from json-big (#1103) ([6435bc1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6435bc1c5f5d9a4c5a9f62d7d0c451292f9d5516))
* package.json & yarn.lock to reduce vulnerabilities (#1092) ([047b4ac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/047b4aca5888790a8576526033c27328091cb238))
* remove duplicate volume mount (#1126) ([0e52c98](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0e52c98ef5ad0c36806640c79830036f35496969))
* requirements/base.txt to reduce vulnerabilities (#1113) ([200512e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/200512e34381bcdc443beb804a7255d08744a2f4))
* scheduled docs with latest_partition fail to run (#1101) ([7b12960](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7b129608d87749525d6aa85cd715cf1a806ab9a7))
* update event_log table schema (#1111) ([3ca3686](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3ca3686cb90ed8952ad154697dbcc5488d79338d))

## [0.48.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.47.0...0.48.0) (2023-01-13)


### Features

* Override HMS Loader to retrieve Cloverleaf-specific details ([b59396e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b59396e58b836a39fd7c00a3fe4a09cb20f74784))

## [0.47.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.46.3...0.47.0) (2023-01-13)


### Features

* add exact error from failed query execution (#73) ([64e6db0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/64e6db025379ad4fbebacd9894564af488c52641))

### [0.46.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.46.2...0.46.3) (2023-01-12)


### Bug Fixes

* Transpile support for external table with JSON file format ([e79de8a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e79de8acab937b6aef6859ee9e06e7e39445f330))

### [0.46.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.46.1...0.46.2) (2023-01-09)


### Bug Fixes

* Configure Flask session cookie properties ([0eec570](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0eec57041265a4cd1721153dcea84cbfc4b610f6))

### [0.46.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.46.0...0.46.1) (2022-12-14)


### Bug Fixes

* Extend DataTableColumn type column length (again) ([f91f359](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f91f359d331817e2f78ef95226a0714c24a5240b))
* Update custom transpiler and enable Presto ([910910c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/910910ccbcc8d48548c15ea97c05993cef5fa3d3))

## [0.46.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.45.1...0.46.0) (2022-12-12)


### Features

* Custom transpiler ([51e5219](https://github.expedia.biz/eg-analytics-platform/querybook/commit/51e5219767dc7f7e1efa1eb366b066986e9aff7b))


### Bug Fixes

* Case-insensitive regexes in the custom transpiler ([2340320](https://github.expedia.biz/eg-analytics-platform/querybook/commit/234032093dcb65e23a65ec99f6984d63224d87ea))

### [0.45.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.45.0...0.45.1) (2022-12-09)


### Bug Fixes

* boost table score for exact match when searching table (#1097) ([d75c1d1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d75c1d1d7089843465f6ecb0a6eb26b67b43c241))
* Keep table search default sort by name ([def3a0c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/def3a0c9562c992d69db00185c7438d77980ebd2))
* notify_user need to accept user not uid (#1095) ([8b5b78f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8b5b78faa35bb2f6dfe7ebef7b3807af4befc3d3))
* remove python-dev from dockerfile build (#1098) ([12520df](https://github.expedia.biz/eg-analytics-platform/querybook/commit/12520df94c9a1543d9a6e726da4c009874ea8e5f))
* remove the edge when the node is deleted in dag exporter (#1089) ([d945a68](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d945a68c92269a8f72a7b3331c2b186e2fcdb378))
* sidebar search should use relevance instead of alphabetical (#1096) ([a18cc93](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a18cc93b49674b0d923ee32b724942cf194ad629))

## [0.45.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.44.0...0.45.0) (2022-12-09)


### Features

* Add EGSlackNotifier with support for v- accounts ([081f8b8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/081f8b82ef8c603721015595dba4e33e462855be))


### Bug Fixes

* Upgrade SQLGlot to the latest version ([0542440](https://github.expedia.biz/eg-analytics-platform/querybook/commit/054244029ed2640fe9a2d0cc1d2e78d940ad7b54))

## [0.44.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.43.0...0.44.0) (2022-12-07)


### Features

* add datadoc retry with delay on failure (#66) ([5d8f87c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d8f87c0c8deaa57715574695370fde1982c2860))

## [0.43.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.42.0...0.43.0) (2022-12-07)


### Features

* Visualize complex Hive column types ([2a98416](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2a9841619050d9f6767a5181d9aed5a1990013fd))


### Bug Fixes

* Extend DataTableColumn type column length ([84b7b71](https://github.expedia.biz/eg-analytics-platform/querybook/commit/84b7b71bacb85f46369555fb55aac40838acdd38))

## [0.42.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.41.3...0.42.0) (2022-11-29)


### Features

* add filter support for api logging (#1084) ([9f1682f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9f1682f1f9983fa0fdbf7f226ce2f60d388d303b))
* add helper task to auto disable unused workflows (#1082) ([a4ce07b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a4ce07b233f7c38dad876a9a3d0075820ab9831b))


### Bug Fixes

* load announcements only if the tab is active (#1085) ([e7779a5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e7779a5237e3f4ea200363d555428b4b789e5a55))
* search and replace overlaps with lint status (#1088) ([1b91cb8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1b91cb8eef5e51ee1de7084a6e59d194c7978c07))

### [0.41.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.41.2...0.41.3) (2022-11-21)


### Bug Fixes

* Revert "fix: package.json & yarn.lock to reduce vulnerabilities (#1020)" ([64bab52](https://github.expedia.biz/eg-analytics-platform/querybook/commit/64bab52021978e478fc5c12fd2ffe951ede8d78f))

### [0.41.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.41.1...0.41.2) (2022-11-21)


### Bug Fixes

* Trino bulk insert exporter configs (#61) ([290b6c5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/290b6c52513f907632be64ebac27e64c32b8e722))

### [0.41.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.41.0...0.41.1) (2022-11-18)


### Bug Fixes

* Add Documentation links to the Landing Page ([1070435](https://github.expedia.biz/eg-analytics-platform/querybook/commit/10704353b348613841b0127e8495bde20a425429))

## [0.41.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.40.2...0.41.0) (2022-11-18)


### Features

* add RangerConnectionChecker (#59) ([5d63eb7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d63eb780dc6ec1bdfe1a3916fdac37c33a6f270))

### [0.40.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.40.1...0.40.2) (2022-11-18)


### Bug Fixes

* Add table upload bulk insertion exporter (#56) ([1a4dbd9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1a4dbd9a6631dca29e4db833069dc76fde58ace8))

### [0.40.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.40.0...0.40.1) (2022-11-18)


### Bug Fixes

* Add SQLGlot requirement to enable query transpiling ([a42312c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a42312c8c6ec2027245c001efad90aebad39c09f))

## [0.40.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.39.1...0.40.0) (2022-11-18)


### Features

* add clock icon for scheduled datadocs in the sidebar ([306fec8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/306fec8d0d734c19ff00216bf50534a61f51823f))


### Bug Fixes

* Alias TaskSchedule in get_scheduled_data_docs_by_user() ([75b6479](https://github.expedia.biz/eg-analytics-platform/querybook/commit/75b64792e8b0ca0b3bd989e4f98f3d64c8df8d6d))

### [0.39.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.39.0...0.39.1) (2022-11-17)


### Bug Fixes

* Add new query suggestions ([c6746f6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c6746f69e0f59171ab07d4beecda6a976567982a))

## [0.39.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.38.1...0.39.0) (2022-11-16)


### Features

* Add custom trino engine status checker plugin (#57) ([1ec53c9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1ec53c92ccfd49a7529da24a7cfe201723c4184b))

### [0.38.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.38.0...0.38.1) (2022-11-16)


### Bug Fixes

* disable some api reqests from event logging (#1079) ([948830c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/948830c5bcf75abfa5320be9bb3bf268d895f11c))
* package.json & yarn.lock to reduce vulnerabilities (#1020) ([37c9af1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/37c9af1e067cb92bfc56ccf9d6c37197b9b40f21))
* relint on engine change + dont show lint when empty (#1077) ([a7d8171](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a7d8171be232b274a69cc9ab1f2d44a312aecb65))
* requirements/dev.txt to reduce vulnerabilities (#1081) ([920ad90](https://github.expedia.biz/eg-analytics-platform/querybook/commit/920ad90615cf6831a4ba2e0cb6dc0d1cdf46fc68))

## [0.38.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.37.2...0.38.0) (2022-11-10)


### Features

* add event logging support (#1075) ([66ba1ac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/66ba1ac2dbd39b93a81eb6fc7fda5913b2f3b440))


### Bug Fixes

* Ensure DataDoc runs get tracked even if template rendering fails (#1073) ([9db0e08](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9db0e08f076e00c0179fd1058732936c828c1627))
* Remove console.log (#1069) ([6827e3e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6827e3eca6f17180523cb34a0c84a066a32af7f3))
* Wrap or truncate long column types (#1070) ([0cbbb42](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0cbbb42d3949166e2ef16c5dce2a49a4bc8ec740))

### [0.37.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.37.1...0.37.2) (2022-11-03)


### Bug Fixes

* Disable unused requirements ([f3e1998](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f3e199878d11899591cb3f29ebdba768535edbee))

### [0.37.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.37.0...0.37.1) (2022-11-02)


### Bug Fixes

* schedule notification exception (#1067) ([281cc5e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/281cc5eb19e70a0db638f94414c13575b1b2bd7b))

## [0.37.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.36.0...0.37.0) (2022-11-01)


### Features

* add customized notification for scheduled datadoc (#1061) ([301c551](https://github.expedia.biz/eg-analytics-platform/querybook/commit/301c551df7888f88d27c6ad71a68d848043feb89))
* Merge branch 'upstream' ([6cd9823](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6cd9823b9f08de7a91c7c86013dce3dd84780a3d))

## [0.36.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.35.0...0.36.0) (2022-11-01)


### Features

* Enable SlackNotifier plugin ([4c93c4a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4c93c4adb74c2af5cb78de16113a46ff4ab037cc))

## [0.35.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.34.0...0.35.0) (2022-11-01)


### Features

* add schema filtering for table search (#996) ([022eaae](https://github.expedia.biz/eg-analytics-platform/querybook/commit/022eaaeb8affdc167fd4e0b80b3f86d378d97b20))
* Merge branch 'upstream' ([859520f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/859520f08ac272278d2b0352dc528297dac816ef))

## [0.34.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.33.1...0.34.0) (2022-10-31)


### Features

* dag exporter v2 (#1058) ([6d034d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6d034d6a104b85bd738181dbbd9896c16f7bfa22))
* Merge branch 'upstream' ([87323e8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/87323e87e347fe91e7532aa2ef952f99ba92cf15))


### Bug Fixes

* [dag exporter] remove use vairables (#1065) ([2ba3372](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2ba3372304c33abe7ec2ce46fc43fda543ddcb2a))
* Add sort_key and sort_order to table search (#1022) ([0be51ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0be51ec39a73728ba18c846f5bc10a1690be90cb))
* only show supported query engines in the current env for dag exporter (#1063) ([27e03ea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/27e03eaf49c3e1bcb4b162f4b8461a10d30f65b9))
* refactored useLint pipeline to be more hooks based (#1066) ([0a0a53b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0a0a53b378bade5d38ec6dee14e9fb72471f4145))
* SqlAutocompler setter not bind (#1062) ([fc521fe](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fc521fe9ad262ec2b7f547ac47c8be17ec5f55d7))
* template variable type change and big numbers (#1046) ([657f2a7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/657f2a74fdd172a6d725ece3265d889b6cdb5ece))
* Update Google OAuth Version (#1057) ([6c4011f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6c4011f606af27af8aca44cbb5c1ceec14a7f1c9))

### [0.33.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.33.0...0.33.1) (2022-10-26)


### Bug Fixes

* Fix null matches on error suggestion ([6cefe86](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6cefe861f8d4e005352610c948245d82de2f735a))

## [0.33.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.32.2...0.33.0) (2022-10-25)


### Features

* Add Starburst logo to the tracking URL ([b95cd9b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b95cd9b96db44636d52d2ee12458044757ccd43a))

### [0.32.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.32.1...0.32.2) (2022-10-25)


### Bug Fixes

* Fix Starburst Tracking Url on multi statement query ([9aaf462](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9aaf462fb58f25c6681b03daba36742787928ca6))
* Remove sync_ldap_task from jobs plugin ([946578f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/946578fe7c8f23210d968c5f2557db4d2385734e))

### [0.32.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.32.0...0.32.1) (2022-10-24)


### Bug Fixes

* Cookie SameSite=none ([e3edd82](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e3edd82298a35467161bf43ae21d22cff2b60fdf))

## [0.32.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.31.0...0.32.0) (2022-10-20)


### Features

* Merge branch 'upstream' ([858fb84](https://github.expedia.biz/eg-analytics-platform/querybook/commit/858fb84f593b47e0a53a0257dd0a521086e7db30))


### Bug Fixes

* QueryComposer additional buttons nested right (#1044) ([9f252e7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9f252e7c38741638e9fdd9c8b8c0aa92b9909794))

## [0.31.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.30.1...0.31.0) (2022-10-20)


### Features

* Add Trino query error suggestions. ([ae36324](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ae363242897b05ff991cd6cad147603f75b31d12))

### [0.30.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.30.0...0.30.1) (2022-10-20)


### Bug Fixes

* Allow row limit of 1,000,000 ([b52b35e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b52b35e5aec465e19edbfd8624af669ba8155c9e))

## [0.30.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.29.1...0.30.0) (2022-10-18)


### Features

* add formatted transpile view (#1031) ([b5120ed](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b5120edb82250c71a9f1a2bf9ff0663da462d93a))
* Add syntax highlight/copy to markdown code (#1039) ([c78fd7f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c78fd7f18d93ce753665426ec4e92fe149a2d147))
* Merge branch 'upstream' ([c84b843](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c84b843d17103993c67b483be6a3a2cb4ecce7e1))
* syntax highlighting for templated queries (#1040) ([12346ea](https://github.expedia.biz/eg-analytics-platform/querybook/commit/12346ea0ed93e5f9890ee5e453eacf9690f0eaa6))


### Bug Fixes

* codemirror starts with a wrong height (#1041) ([a2d7463](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a2d746364478016badc769be470da8d556fb8dd8))
* ExecutedQueryCell auto scropll to top during execution (#1033) ([011bb92](https://github.expedia.biz/eg-analytics-platform/querybook/commit/011bb92435dd6d59a85afb57041fecbdd548f096))
* formatQuery isn't using the latest ref (#1042) ([7f02f09](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7f02f0993cfba4756731e559d3b4fddd0204043f))
* query editor issues after refactor (#1035) ([3faf4bb](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3faf4bb7e588b6ed76c5aa1eafaf9f81827859fd))
* table column auto completion not work sometimes (#1026) ([72bd343](https://github.expedia.biz/eg-analytics-platform/querybook/commit/72bd343dd5b39fee8fa4d093069d839167539b9f))

### [0.29.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.29.0...0.29.1) (2022-10-17)


### Bug Fixes

* Pin trino client to the latest working version ([fd39962](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fd399627d1a6750cc499e7f5cfdcc6b7a576c6b4))

## [0.29.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.28.0...0.29.0) (2022-10-05)


### Features

* Merge branch 'upstream' ([0abf791](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0abf791bd85a27533ddf5e58793231ff2313d93f))


### Bug Fixes

* disable autocomplete for exact matches (#1029) ([1952973](https://github.expedia.biz/eg-analytics-platform/querybook/commit/19529731d450a093fd909c52949fb7f2001d32e5))
* Increase CodeMirror hint z-index above modals (#1030) ([96c44f9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/96c44f98ef17d51fabc188912cb4ac5a2c25db45))

## [0.28.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.27.0...0.28.0) (2022-10-05)


### Features

* Merge branch 'upstream' ([2c832e1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2c832e15ef698080a25f57b45cfbff671c3dd650))


### Bug Fixes

* Replace cronjs-matcher with cron-parser (#1028) ([edefd6b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/edefd6b799e8c2c06b7bece97271f0a583d8f77b))

## [0.27.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.26.1...0.27.0) (2022-10-04)


### Features

* Merge branch 'upstream' ([1a87804](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1a87804d0ba46ce7b7578ce1de1f9fe09d793ef2))


### Bug Fixes

* Automatically enable JSON transformer ([060c661](https://github.expedia.biz/eg-analytics-platform/querybook/commit/060c6616db8eebeadda7139e577c21f5411d0263))
* disable json parsing by default (#1025) ([d42ec00](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d42ec003727b538db9b24f441afc7a4494b0d78e))
* Make Presto Explain Validator optional install (#1023) ([fab8d80](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fab8d804cdf8e787d553a6512d9335235d894c26))
* schedule owner not update (#1027) ([06c7995](https://github.expedia.biz/eg-analytics-platform/querybook/commit/06c7995a2ddeee9cbd6608fd4b055f6825dfab37))

### [0.26.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.26.0...0.26.1) (2022-10-03)


### Bug Fixes

* Update Trino tracking url to go to query overview instead of query's plan ([0f42205](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0f42205eeec6ca1fad3e2fc5ef43b04325f31d9f))

## [0.26.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.25.0...0.26.0) (2022-09-27)


### Features

* (experimental) make error suggestion pluggable (#1017) ([3a5eb97](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3a5eb97a26a7bcbb419144a34dda78a5b2c52cea))
* Merge branch 'upstream' ([00ac4cf](https://github.expedia.biz/eg-analytics-platform/querybook/commit/00ac4cfc0875da8a4912fd63bb0d100b764b5ce0))
* show deactivated user with different ui (#1014) ([3fd594f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3fd594fbfb0567f3adc29272a5c11ca38d9673b3))


### Bug Fixes

* do not transform presto map keys (#1021) ([bd73970](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bd73970e9f37d73584da7f37a123488d5ff849c8))
* JSONView fix (#1019) ([0b810c2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0b810c2f0a991c7c896ed54672db1be1ba0f8cd6))
* userInfo might be null (#1016) ([ca2f1bc](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ca2f1bc8ea32f14729d2f4c73980172c9a19ddc9))

## [0.25.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.24.1...0.25.0) (2022-09-23)


### Features

* Disable UI access to create API tokens ([1fd56fb](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1fd56fb5feda059e8b86d12e49d58938c3564710))

### [0.24.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.24.0...0.24.1) (2022-09-23)


### Bug Fixes

* Fix EG Trino/Starburst executors ([73cd375](https://github.expedia.biz/eg-analytics-platform/querybook/commit/73cd375f176fac67967fbc7e1d6f0002ce3316bd))

## [0.24.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.23.1...0.24.0) (2022-09-23)


### Features

* display presto and trino nested structures (#991) ([c4ecff4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c4ecff42df93da58316852520b189ac2a744c0f4))
* Merge branch 'upstream' ([dc09429](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dc0942938b28443cd05561427ba10aac88bd9a52))

### [0.23.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.23.0...0.23.1) (2022-09-21)


### Bug Fixes

* Enable Flower container deployment for Celery (#37) ([790d03a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/790d03a6818a58fdbfaf4c0b23176b32ca2519d4))

## [0.23.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.22.0...0.23.0) (2022-09-21)


### Features

* Merge branch 'upstream' ([bee24ef](https://github.expedia.biz/eg-analytics-platform/querybook/commit/bee24ef249b2833b97be207aed7aab97325a845c))


### Bug Fixes

* delete button stuck in spinning for cancel confirm (#1012) ([dfe0905](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dfe0905ddab12ef7075a6c280f9f56405576b5be))
* url validation (#1013) ([65767f7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/65767f73fa1798fd2477d2fd78136363e182336a))

## [0.22.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.21.1...0.22.0) (2022-09-20)


### Features

* add diff view when transpiling query (#1010) ([225b0ac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/225b0ac20717cd7bad2196387f34e891896003f5))


### Bug Fixes

* automatic serialize sqlalchemy Row (#1011) ([372ab25](https://github.expedia.biz/eg-analytics-platform/querybook/commit/372ab25436cd0dd7b0846d7545b3255dbe5876c9))
* table validation for sync_table (#1008) ([760b6ec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/760b6ec0dd3715058b138b528657cc62558d27a5))

### [0.21.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.21.0...0.21.1) (2022-09-15)


### Bug Fixes

* Table upload fixes ([4bf9563](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4bf9563fbec6aa9617c6447943e73255fbd4aa80))
* Undo remove replace ([965973c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/965973c2fa41ef65ef349985065304cc8a9df0b6))

## [0.21.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.20.3...0.21.0) (2022-09-15)


### Features

* Add a new function to sync table with metastore (#998) ([6ffe0ff](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6ffe0ff48d99045f0b73b1831978b0b752d8e940))
* allow user to bypass LIMIT (#1000) ([e9d11ed](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e9d11edc8c8a96102ab2d7d9487f95c669c22a82))
* improve charting axis and value display (#999) ([3b36df2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3b36df2bd9aaa4874715a3754824a458c08e9e6f))
* improved query limit (#995) ([64f6e60](https://github.expedia.biz/eg-analytics-platform/querybook/commit/64f6e60ef0517a4c6f315882d94bc088bdaa4842))
* Merge branch 'upstream/master' ([88abf71](https://github.expedia.biz/eg-analytics-platform/querybook/commit/88abf71f93301c09ea80af8412d95c3b877cfc8d))
* pass execution type to executor client (#992) ([5f3a961](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5f3a9613aabbcc8f9eb47d5e197ff41f1dd55915))
* show 404 page when table gets deleted (#1003) ([37a9434](https://github.expedia.biz/eg-analytics-platform/querybook/commit/37a94345884f934ab9c7d11a4ae088b4ecafdb63))


### Bug Fixes

* add acl check for metastore table sync (#1004) ([fdb5df0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fdb5df09480d9c0beb2f1ef38d755dae5c55ab96))
* disable new features in read only mode (#1002) ([5fa45d7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5fa45d7e292ecf34dd3260f23bc468eed3fa7e83))
* Hide export option on scheduler pop-up if there are no exporters available (#1001) ([d8a3112](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d8a31125e4700b1acb4d7f5349e202786db32f0f))
* lint error doesn't disappear when switching to templating query (#994) ([a859d7a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a859d7a267e3ea7bb187d4c771b4aff81609a5c5))
* raise rate limit for the sync api (#1007) ([0251ffd](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0251ffdd23cd25ab8ee5003f47926848d15a802e))
* transfer schedule's ownership along with datadoc's ownership (#1005) ([8732d97](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8732d9793ad6d3dbdd809bb23dea9535c7842acf))

### [0.20.3](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.20.2...0.20.3) (2022-09-13)


### Bug Fixes

* Manually fix alembic migration order (again) ([b5b7376](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b5b73760da25e2935b685ea62f922e826cfe2a01))

### [0.20.2](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.20.1...0.20.2) (2022-09-13)


### Bug Fixes

* Manually fix alembic migration order ([e31a70a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e31a70a5c0166117d02d663e9f9ee77149eef154))

### [0.20.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.20.0...0.20.1) (2022-09-13)


### Bug Fixes

* Create new executor for Starburst ([7839aa7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7839aa702b50c029664cdc4d0ca90648d3017341))
* Remove prints ([5d372a1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d372a16b827eef30de026fe45286ba835955fad))

## [0.20.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.19.1...0.20.0) (2022-09-08)


### Features

* (experimental) add Query transpilation to Querybook (#988) ([cbf650a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cbf650a7f0a5dbae16419b0c05f50adf043d3c0d))
* Add a new API of syncing a table from metastore (#982) ([c0e1dec](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c0e1decfe69cd5919779d7b5504e6c9d516ad76e))
* add icon for partition keys (#977) ([ca62466](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ca62466b853eb1b3d2523bcabb44d49eafc000e6))
* add query validation to querybook (#984) ([7069dac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7069dac81169dacea27f884e770dce079e38d469))
* add support of syncing table/column description from metastore (#980) ([b8a3eb5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b8a3eb576a0039b66e8838f20bd1b3ceeae0bd94))
* improve table upload with managed/external (#979) ([156d020](https://github.expedia.biz/eg-analytics-platform/querybook/commit/156d02086d7363757a52b1b34db8199c6fe40c50))
* Merge remote-tracking branch 'upstream/master' ([394f0da](https://github.expedia.biz/eg-analytics-platform/querybook/commit/394f0daf3e9805358026d591066e63b636e56041))


### Bug Fixes

* column icon css for partition keys (#987) ([6b08a88](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6b08a88d97fd515c2d74fde10d5b13f6a2a92bbf))
* **DataDoc:** Use Previous Query Engine (#983) ([1ef498b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1ef498be2c1e4924c00bce652b0c21f2cea1058d))
* docs website failed to build (#981) ([970628d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/970628df6ec51b0f907b8ce00ab9e073ff0222f9))
* overflow in raw metastore info (#976) ([339b2ce](https://github.expedia.biz/eg-analytics-platform/querybook/commit/339b2cee4c7f9d1bc0ca2cafb414a9be40130325))
* scatter/bubble charts were losing their labels after save (#985) ([0ae4659](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0ae46596480e158c4466e0fee531c4c290207fe4))

### [0.19.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.19.0...0.19.1) (2022-09-07)


### Bug Fixes

* Set source property as 'querybook' in Trino connection ([e08b1a8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e08b1a887d2b7e5736181ba11b32fda928421593))

## [0.19.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.18.1...0.19.0) (2022-08-24)


### Features

* Display better error message to users without access ([3efd6ee](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3efd6eef9b4481690e038995de5729d1ed02da73))

### [0.18.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.18.0...0.18.1) (2022-08-23)


### Bug Fixes

* Implement impersonation on Trino Exporter for table upload ([560aa1c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/560aa1c118d786c8f0852bce2864947c0be2c4e8))

## [0.18.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.17.1...0.18.0) (2022-08-23)


### Features

* Add `feature_params` to Environments ([5b115e7](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5b115e74c7595113bbe0fd96b7a706689934a03e))
* Additional access control settings for Environments/Query Engines ([6d3ab79](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6d3ab79446b4b4aed8bdb0c59fc1f42eaf839942))
* Configurable AD sync for Environments, Query Engines ([060494b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/060494bd46e0dd4fafe2bbb7e7c418df63623ca4))

### [0.17.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.17.0...0.17.1) (2022-08-22)


### Bug Fixes

* Convert engine_id from str to int ([874bd4c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/874bd4cc566c1ef7e698bbf344cf27855733d48f))

## [0.17.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.16.0...0.17.0) (2022-08-19)


### Features

* Add global_groups to sync groups to all environments ([32ae596](https://github.expedia.biz/eg-analytics-platform/querybook/commit/32ae596a39931ab83083fdf4171f6be4482a5e47))


### Bug Fixes

* Add Trino exporter for table upload (#13) ([9dc2b79](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9dc2b799aa5418a51b33be93bc683bdc24c9a1aa))

## [0.16.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.15.0...0.16.0) (2022-08-18)


### Features

* Adds access control to Query Engines ([6e2bb11](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6e2bb11fdde5703562a01d5f86ed1571e96e15c5))

## [0.15.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.14.0...0.15.0) (2022-08-18)


### Features

* Automatically add a row limit to queries ([8cda37e](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8cda37eb2fcda211f01bb1bc4cfc3872325d4e5e))
* Split Trino and Presto language, add Trino-specific keywords ([a7b716f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a7b716f4d01c1389eee4c4d4f2a748d909ad450d))


### Bug Fixes

* Extend sql-limiter to support nested queries and union queries ([ca5b510](https://github.expedia.biz/eg-analytics-platform/querybook/commit/ca5b510dfe4879feaee31b751b40c979cbd2ebf0))
* Use Okta preferred username ([6dcc75c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6dcc75c25b71e9c2161068bee1e675de644e2c8e))

## [0.14.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.13.1...0.14.0) (2022-08-17)


### Features

* Add eg_trino_executor ([c961d4a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c961d4ad24f167ee4c4b81158ab020f46bee3bea))
* Add plugin executor to include Json and CSV warnings ([0b34eb9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/0b34eb9e55fcd5dccc5cff939dd67b068f88d8cc))

### [0.13.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.13.0...0.13.1) (2022-08-16)


### Bug Fixes

* Change debug logs to info and add more logs ([fa000fc](https://github.expedia.biz/eg-analytics-platform/querybook/commit/fa000fc46f2c2ad9246630448a28a4c0d91981b6))

## [0.13.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.12.0...0.13.0) (2022-08-16)


### Features

* AD Sync Task ([232d036](https://github.expedia.biz/eg-analytics-platform/querybook/commit/232d0366be606552a90a83d76f2b3487cbd20e00))

## [0.12.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.11.1...0.12.0) (2022-08-15)


### Features

* Add breadcrumb for board in querybook (#962) ([5d06c0f](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5d06c0f486889855cffc44365545775da58af4f6))
* add table name drop and drop (#952) ([8e330d3](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8e330d315fac2f5f975f03a17f574606fb2e71fe))
* Allow executors to return warnings for query executions (#963) ([f766f29](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f766f294d1bc187b3780bf4f21ea2fd60f9dc92d))
* dont show stack trace is exception is recognitizable (#957) ([06a54d6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/06a54d68b597a5de7499c9adba71121ff422121e))
* Ignore null values when detecting types (#958) ([4e977b4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4e977b48eb46910462fcec045f7e4e23d57aa432))
* Merge remote-tracking branch 'upstream/master' ([dd71995](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dd71995fc0cf0dd6770c47bb4f573e3c0edd45b1))


### Bug Fixes

* auto add trailing slash at end (#965) ([12e7519](https://github.expedia.biz/eg-analytics-platform/querybook/commit/12e751930094f4bc5707177a1160a2e82c9aca49))
* DELETE http does not work without params (#954) ([8ac6cde](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8ac6cdee89b8322d1c7660877cb4423b2556598b))
* docs_website/package.json & docs_website/yarn.lock to reduce vulnerabilities (#951) ([0576134](https://github.expedia.biz/eg-analytics-platform/querybook/commit/057613426646b4c8f95756b54f3367a483ffe1b9))
* Prod build fails to install uwsgi (#955) ([5466fd8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/5466fd8bc01933d21cfc610b90a0e7fe794f10e7))
* revert back to python 3.9 (#956) ([214118c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/214118c2137dfec580cba5dbeb4e0a19351f3c62))

### [0.11.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.11.0...0.11.1) (2022-08-05)


### Bug Fixes

* Fix readonly attributes ([df33776](https://github.expedia.biz/eg-analytics-platform/querybook/commit/df33776727870708e3257bc09caba4c38bc66a8c))
* Use internal Docker repository ([2be85f0](https://github.expedia.biz/eg-analytics-platform/querybook/commit/2be85f0d9d4a2ea3bf8f84c92aca4c46e899234f))

## [0.11.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.10.1...0.11.0) (2022-08-01)


### Features

* add 'All' button in the 'Hide columns' menu (#949) ([4f978ed](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4f978edf65bdd1dc64a7b6e12d6eae9f5ba90a87))
* add confirmation before execution if the query drops any tables (#946) ([9eb303b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/9eb303b423b3b459c379563f98addc1540a6fd62))
* add Multi-line and multi-cursor editing (#941) ([127e7e4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/127e7e4157dad278821b745738612cf3f73a66cf))
* Add templating support for Adhoc query (#939) ([53e88c9](https://github.expedia.biz/eg-analytics-platform/querybook/commit/53e88c962d81f3c6eb74e47b4baa52433d541b30))
* Merge remote-tracking branch 'upstream/master' ([6f75e43](https://github.expedia.biz/eg-analytics-platform/querybook/commit/6f75e4396af265a2f3567124f360c79f8fb52b10))
* Update Okta auth method to provide full names (#945) ([7438cac](https://github.expedia.biz/eg-analytics-platform/querybook/commit/7438cac676485a700c4997f11d437556af201e09))


### Bug Fixes

* adhoc template query (#944) ([a443f2b](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a443f2bfedf2cd8c40a51098c59843041f349bdb))
* getStatementType vs invalid queries (#948) ([82996b2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/82996b2072a771f9a4f61a9cdc123ddf7fb4466e))
* list drag and drop (#938) ([d03f88d](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d03f88d3aec37e8d09e3915106f4b3ef64f3642e))
* various board related bugs (#943) ([f7e85f8](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f7e85f8d4dd0a85f33c961efcd8d0fdbbef7233f))

### [0.10.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.10.0...0.10.1) (2022-07-28)


### Bug Fixes

* Install some additional packages ([4c827b4](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4c827b45d5c3919989ddd488038862f532268b91))

## [0.10.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.9.0...0.10.0) (2022-07-20)


### Features

* Add auto updating timestamp (#936) ([cb668cb](https://github.expedia.biz/eg-analytics-platform/querybook/commit/cb668cb6b12ba3955ef0e6c95838a8eee925246b))
* Collapse and expand ad hoc query execution results (#937) ([8e1e7c6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/8e1e7c67dcb0ea341d8d4321c830371773333508))

## [0.9.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.8.0...0.9.0) (2022-07-15)


### Features

* add username+password authorization into Trino client ([dfb68a2](https://github.expedia.biz/eg-analytics-platform/querybook/commit/dfb68a2539d737b2e52fa09e2e3aff7c11f40346))

## [0.8.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.7.0...0.8.0) (2022-07-14)


### Features

* add auto url transform to querybook (#918) ([4ec198c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/4ec198cb0ed30662424b3f3a4e81abc8f0eb2a4d))
* list ver 2.0 (#925) ([e5ceb4c](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e5ceb4c7af98bef1bf3980dc17dd9db9a0d08949))
* Merge remote-tracking branch 'upstream/master' ([99265c5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/99265c51c6e86ee977210f7f4bf2cba5128515b1))
* strip white space when rendering templated queries (#919) ([d6a11c1](https://github.expedia.biz/eg-analytics-platform/querybook/commit/d6a11c1100fc503b61eafe26953189af26e0a256))


### Bug Fixes

* combine update es queries by datadoc id into one celery task (#933) ([eab29ce](https://github.expedia.biz/eg-analytics-platform/querybook/commit/eab29ced4243954ee1d6acce68547592ccf846ef))
* draftjs backend parser (#927) ([c46a793](https://github.expedia.biz/eg-analytics-platform/querybook/commit/c46a793e996afe3113e700f790d03100c59cba2f))
* package.json & yarn.lock to reduce vulnerabilities (#926) ([a37dfcc](https://github.expedia.biz/eg-analytics-platform/querybook/commit/a37dfcc9fb880898b786dd0553f7c8edb30dec04))
* Pin protobuf to 3.20.1 (#917) ([e146512](https://github.expedia.biz/eg-analytics-platform/querybook/commit/e1465121d3659069b24eb5b2e5f67acfdf06658f))
* rich text editor issues (#914) ([49930d5](https://github.expedia.biz/eg-analytics-platform/querybook/commit/49930d5c10397cfdf2e379cd9d1a35ca9bab8d4d))
* various board and search updates (#934) ([f9f9763](https://github.expedia.biz/eg-analytics-platform/querybook/commit/f9f97633f3e45d8b7abcabf93d34bc4cedd46bb5))

## [0.7.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.6.1...0.7.0) (2022-07-11)


### Features

* Add additional config file ([3e48456](https://github.expedia.biz/eg-analytics-platform/querybook/commit/3e4845672e9b7ddb7e10a081c29f737d61bdc330))

### [0.6.1](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.6.0...0.6.1) (2022-07-06)


### Bug Fixes

* **expedia:** Add Expedia SSL certificates, load environment variables from `.env.local` ([519275a](https://github.expedia.biz/eg-analytics-platform/querybook/commit/519275a9159c2a46e639a1b1c0b7b54491658474))

## [0.6.0](https://github.expedia.biz/eg-analytics-platform/querybook/compare/0.5.0...0.6.0) (2022-07-01)


### Features

* add auto url transform to querybook (#918) ([1fd45df](https://github.expedia.biz/eg-analytics-platform/querybook/commit/1fd45df480b1e5a4d355cd89ee7cf0a03f04b448))


### Bug Fixes

* Pin protobuf to 3.20.1 (#917) ([b8a00c6](https://github.expedia.biz/eg-analytics-platform/querybook/commit/b8a00c690fc4c4d3d95c8b0f2a156ae9912cd9bb))
* rich text editor issues (#914) ([09ec7ab](https://github.expedia.biz/eg-analytics-platform/querybook/commit/09ec7abab3a1730207b7847b8fbeffcb3bfab5e5))
