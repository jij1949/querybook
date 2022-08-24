# Changelog

All notable changes to this project will be documented in this file. See [Conventional Commits](https://conventionalcommits.org) for commit guidelines.

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
