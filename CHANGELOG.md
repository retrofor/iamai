# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.8] - 2024-11-25
### New Features
- [`cfd9192`](https://github.com/retrofor/iamai/commit/cfd91928a78a053c2d60226a7b60f06f426fa36c) - add zhCN i18n language support *(PR [#305](https://github.com/retrofor/iamai/pull/305) by [@BegoniaHe](https://github.com/BegoniaHe))*

### Bug Fixes
- [`ac24df0`](https://github.com/retrofor/iamai/commit/ac24df063b200409f17cb2890027f0b617403338) - **publish-docker**: correct version extraction from tag *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`764ca16`](https://github.com/retrofor/iamai/commit/764ca162fa623b33294e7a44c2f77453573b6968) - fix the issue of incorrect hash value in the lock file *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Refactors
- [`6bb6ec9`](https://github.com/retrofor/iamai/commit/6bb6ec972e94d32189304aa43895147fcdf8324c) - **.github**: Update Node to v18, Python to v3.9, and optimize workflows *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4610cea`](https://github.com/retrofor/iamai/commit/4610cea1206ba38d1c9044c38155c5ffec728638) - **iamai**: Remove unused import and update __all__ *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`5211ab1`](https://github.com/retrofor/iamai/commit/5211ab111e4cb5f973d88ebd295bfb8b04043a08) - **publish-docker**: restrict image push to tags only *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`c430cc7`](https://github.com/retrofor/iamai/commit/c430cc7c6c16ff7f115496e0bbc5192c3f846171) - remove unused French and Chinese translation files *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3886c8d`](https://github.com/retrofor/iamai/commit/3886c8d35c2fc02dffe22184089b2f2f85be9a8c) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.1.7] - 2024-11-11
### New Features
- [`c47789c`](https://github.com/retrofor/iamai/commit/c47789c8c3bfde9d9e8c3d69a429e6f242256d43) - update CI workflow to publish to PyPI and Docker with inputs and secrets *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`16197f5`](https://github.com/retrofor/iamai/commit/16197f5ba4861c2cc6c70fa0c70d76d7d16b933a) - update CI workflow to publish to PyPI and Docker with inputs and secrets *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`c115ba4`](https://github.com/retrofor/iamai/commit/c115ba466ee3fc0c46ed3a2453d0397c6f9638b3) - update CI and Docker workflows for publishing and image pushing *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`cc4afd6`](https://github.com/retrofor/iamai/commit/cc4afd61140a29dd3c55caf2ae7c35a4678622dd) - remove git-webhook code and related config in examples *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`8c20d25`](https://github.com/retrofor/iamai/commit/8c20d251eecb46f41b5de92613ed630fa837e4e3) - I18n support and optimize output messages *(PR [#291](https://github.com/retrofor/iamai/pull/291) by [@HsiangNianian](https://github.com/HsiangNianian))*
  - :arrow_lower_right: *addresses issue [#292](https://github.com/retrofor/iamai/issues/292) opened by [@HsiangNianian](https://github.com/HsiangNianian)*
- [`a012626`](https://github.com/retrofor/iamai/commit/a012626f7b3cab06c556af0e6a264eccc66ccaa8) - **.github**: add HsiangNianian to GitHub Sponsors *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`29c498d`](https://github.com/retrofor/iamai/commit/29c498d2f569d92a026568a4e5f5a75adf1f346f) - add Deu i18n language support *(PR [#303](https://github.com/retrofor/iamai/pull/303) by [@BegoniaHe](https://github.com/BegoniaHe))*

### Refactors
- [`0796c98`](https://github.com/retrofor/iamai/commit/0796c989c467a9aed1250a748f15fa7bb286842f) - **.github/workflows**: comment out PyPI publish step in release.yml *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`df0b61a`](https://github.com/retrofor/iamai/commit/df0b61a5091a42364f64d38d7cd853b343a353ae) - update Docker workflow to build and push image with ghcr and login with Github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`d8895dc`](https://github.com/retrofor/iamai/commit/d8895dc7cfec5f9601ffcb3f83bfd92822904766) - update workflow to build and push docker image with ghcr and login with github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`877534d`](https://github.com/retrofor/iamai/commit/877534db5da2d3bbaf8575dc4b6861e13e48d7bf) - update docker workflow to push image to ghcr with sudo and log in with github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`dd80f47`](https://github.com/retrofor/iamai/commit/dd80f47689caa0359d11f2d6da51ccefcb6fdf2d) - update Docker workflow to push image to ghcr with sudo and log in with github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`6ffe668`](https://github.com/retrofor/iamai/commit/6ffe668a59c27f7a07f7b85f647ac1f08360bfbc) - update dependencies and remove unused crates in Cargo.lock and Cargo.toml *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`cfb084f`](https://github.com/retrofor/iamai/commit/cfb084f728c4aae269628712d125f3759b5901c9) - remove unused doc comment and module docstring in libcore *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3aa3d6c`](https://github.com/retrofor/iamai/commit/3aa3d6c2174c406f1824e438af3ddfbd7a06e0a3) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`6d714d6`](https://github.com/retrofor/iamai/commit/6d714d601c08ba30fe12429c2a38631c641c8c7b) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4903d83`](https://github.com/retrofor/iamai/commit/4903d83f6102edb78a6e733824e3fbe7de435c79) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`288453c`](https://github.com/retrofor/iamai/commit/288453cd74e2b87f6a637e196da6159f82afa177) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`5ff8101`](https://github.com/retrofor/iamai/commit/5ff81016b85fb54d641c9b157621ad30fad375d8) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`e95d288`](https://github.com/retrofor/iamai/commit/e95d288a6c382f1635a9bc0d6bfc19810300032f) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`343faa8`](https://github.com/retrofor/iamai/commit/343faa8d052dfbb5378ffcbfab8ca7b70e0af271) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`926804e`](https://github.com/retrofor/iamai/commit/926804ec3f1e35cd2674587c13a56aaf96febaf0) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`708f521`](https://github.com/retrofor/iamai/commit/708f5216317d613feaa2e9d1e5087439bf6cb6ce) - bump version into 0.1.7 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`c485f60`](https://github.com/retrofor/iamai/commit/c485f604156cfb66a87b9c9fe1b461a1650b3df3) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.1.6] - 2024-09-24
### New Features
- [`9e7052d`](https://github.com/retrofor/iamai/commit/9e7052d89ca0ef34fd74eeb0bfb9d49b22ccf9da) - update docker workflow to push image to ghcr and log in with github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Bug Fixes
- [`5d71933`](https://github.com/retrofor/iamai/commit/5d719338e6e365812662ca8f41d71d27f0fd0736) - update workflow to build and push docker image with ghcr and login with github token *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`e8aa048`](https://github.com/retrofor/iamai/commit/e8aa048379810363adc95e41c9016621e51363cb) - update docker workflow to newer actions and remove sensitive info *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4e5a751`](https://github.com/retrofor/iamai/commit/4e5a751f9976b3e604bdbccfc44769b7b0e6c6d3) - update docker workflow to push image to all registries *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`9400bbe`](https://github.com/retrofor/iamai/commit/9400bbe519e0cf7e3b7f02ea2c98d07b1ba186e7) - update versions and dependencies in pyproject.toml files *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.1.4] - 2024-09-24
### New Features
- [`01daf68`](https://github.com/retrofor/iamai/commit/01daf68a15bd92198ec18fa9ca9291e9115dbd80) - update dependencies and modify api build actions *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`a9660d6`](https://github.com/retrofor/iamai/commit/a9660d6627fa72966e99a617eb80d707e8843af6) - update dependencies and fix legacy documents *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`0600301`](https://github.com/retrofor/iamai/commit/0600301c31e87868f1329a56bc3534a555aa6c33) - **docs**: hardcode project info for sphinx *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`59f567e`](https://github.com/retrofor/iamai/commit/59f567ec0214fa14dbd73fca764a48726f9d46e3) - **docs**: update changelog and remove unused adapters *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`e06b50d`](https://github.com/retrofor/iamai/commit/e06b50d0dedf66f7185fb9e935efd309a844cabf) - **docs**: update requirements and add sphinx-last-updated-by-git *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`c8f4937`](https://github.com/retrofor/iamai/commit/c8f493727f6f5f3f8634c174bb844ff27dac5bf9) - **docs**: update credits with Apache 2.0 and other licenses *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`f715368`](https://github.com/retrofor/iamai/commit/f715368caeacd07111b2d969523f3581fd3ce659) - **docs**: enable translation progress classes in sphinx *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`ae74d3a`](https://github.com/retrofor/iamai/commit/ae74d3a5384e8beb928ec0c0cd604de59a2cd708) - **docs**: hardcode project info for sphinx *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`913b48d`](https://github.com/retrofor/iamai/commit/913b48dd4148f9301dd5c1d5f7e7414839aaa778) - **docs**: update translations and add missing strings to the Chinese version *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`fb7bba3`](https://github.com/retrofor/iamai/commit/fb7bba35204e2839900427f6392ea7c8ed388c4e) - **docs**: update pdm installation command in gitpod *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`52cad91`](https://github.com/retrofor/iamai/commit/52cad9139de4589bbad9038f8baf95d4de5df9ef) - **build**: update dependencies for pdm lock file *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3d17553`](https://github.com/retrofor/iamai/commit/3d17553411ceb1b643eff369c881c7c84dadb6ac) - **build**: update base image and install python dependencies *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3e0fc94`](https://github.com/retrofor/iamai/commit/3e0fc945626f63c196a8b988a936caa84553553f) - update iamai and adapter versions and dependencies *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Bug Fixes
- [`6c1eb3e`](https://github.com/retrofor/iamai/commit/6c1eb3e953af01f10ea1e61ceaca31c5ec153ed1) - legacy documents remained due to the wrong step in workflow *(PR [#287](https://github.com/retrofor/iamai/pull/287) by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`3740ef1`](https://github.com/retrofor/iamai/commit/3740ef13df2b3ea5e22f82e7f26c2e22655e0a8f) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`52b107d`](https://github.com/retrofor/iamai/commit/52b107d11571628154b4561ea1e624434dbc1722) - **readme**: add bibtex for cite usage *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`f503686`](https://github.com/retrofor/iamai/commit/f5036866e7e2ca39521f7eeead706c0889e58778) - **workflow**: remove branches from release workflow *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`fdbe7ec`](https://github.com/retrofor/iamai/commit/fdbe7ecf7454db10bb82925bafbf47922709ea1f) - update license MIT -> AGPL3.0 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3d56903`](https://github.com/retrofor/iamai/commit/3d56903a0c4ea5d34d609eb22a871bb9373007a7) - delete uv.lock *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`bb3da6f`](https://github.com/retrofor/iamai/commit/bb3da6fe0bbf1595c1b12c19e97fcbc6ca6263ff) - update dependencies and target versions in pyproject.toml *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.4] - 2024-08-11
### Chores
- [`e4f6b7b`](https://github.com/retrofor/iamai/commit/e4f6b7bcfbc00b73d7b43ea747e1f4fe06bb05ee) - bump version in to 0.0.4 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3-rc.4] - 2024-08-11
### BREAKING CHANGES
- due to [`9e9aeed`](https://github.com/retrofor/iamai/commit/9e9aeed12a501901425d6b782879c1260b608d1f) - fix @actions/upload_artifact@v4 breaking changes for upload same name files *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*:

  fix @actions/upload_artifact@v4 breaking changes for upload same name files


### Bug Fixes
- [`48d4a55`](https://github.com/retrofor/iamai/commit/48d4a55d7de5c52d22f863067a08c2d2bb8487c4) - dynamic fix compile error *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`8588182`](https://github.com/retrofor/iamai/commit/8588182bd89f00ff500fe3762bb5091a0733bed8) - **adapter**: refactor kook adapter event, exceptions *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Refactors
- [`df1bf4d`](https://github.com/retrofor/iamai/commit/df1bf4d916de9790a13332d271e5aa3236ccaa1d) - **project**: build with rust *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`dd5aa72`](https://github.com/retrofor/iamai/commit/dd5aa720b0a1e6925a70242398b91cda3f10833c) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`81de1d6`](https://github.com/retrofor/iamai/commit/81de1d694398658c9e619c36fbca40130a0f4f55) - **project**: remove useless files *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`5db979b`](https://github.com/retrofor/iamai/commit/5db979bb8e0b759fc934ae82dd4d1638589f5421) - **lint**: format with ruff *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`ed5a1a0`](https://github.com/retrofor/iamai/commit/ed5a1a0b21d34acaebe133ff1900090b09041fc0) - **deps**: update dependencies *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4314aa9`](https://github.com/retrofor/iamai/commit/4314aa900b489e5b4ed1110e5aa4109ba3cb657a) - add .ruff_cache to the ignore list *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`1ae75c8`](https://github.com/retrofor/iamai/commit/1ae75c8761f659c0830e2abadd0b510cf6ee526b) - **lint**: format code *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`3f881c8`](https://github.com/retrofor/iamai/commit/3f881c8d3ef5d86e876019a9bf305f4860578aeb) - **deps**: bump actions/download-artifact from 3 to 4 *(PR [#280](https://github.com/retrofor/iamai/pull/280) by [@dependabot[bot]](https://github.com/apps/dependabot))*
- [`ee0070c`](https://github.com/retrofor/iamai/commit/ee0070cf0c0852fc1fe9d35bf8be048d37f4333c) - **deps**: bump actions/upload-artifact from 3 to 4 *(PR [#279](https://github.com/retrofor/iamai/pull/279) by [@dependabot[bot]](https://github.com/apps/dependabot))*
- [`34c8b52`](https://github.com/retrofor/iamai/commit/34c8b5230c14813de7d92d3750bef356c59b51f0) - bump version into 0.0.3-rc4 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`7d1e1ab`](https://github.com/retrofor/iamai/commit/7d1e1ab203326dd3dfdec11b0164966d99baa884) - rename version *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`00d0bdb`](https://github.com/retrofor/iamai/commit/00d0bdbdfa0a1bcaccb19ae3d6dbc28b2203aeba) - rename version *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3rc3] - 2024-02-23
### BREAKING CHANGES
- due to [`a09bf3f`](https://github.com/retrofor/iamai/commit/a09bf3f8a25693c0f28f1e332c4391529fa69f16) - rewrite kook, apscheduler adapter *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*:

  rewrite kook, apscheduler adapter


### Refactors
- [`a09bf3f`](https://github.com/retrofor/iamai/commit/a09bf3f8a25693c0f28f1e332c4391529fa69f16) - **adapter**: rewrite kook, apscheduler adapter *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`e3f9845`](https://github.com/retrofor/iamai/commit/e3f98452af7178d767cd72335fe4a6febd0cd042) - **project**: bump version to 0.0.3rc3 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3b5] - 2024-02-23
### Bug Fixes
- [`76fa3e0`](https://github.com/retrofor/iamai/commit/76fa3e0cf3f1120df68c817c0a3e2cb9f23e631e) - **workflow**: rename "onebot11" to "cqhttp" *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`4fe3918`](https://github.com/retrofor/iamai/commit/4fe39182a361eb60b559ee57a3a956e0757a1128) - **readme**: upate *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`bae16f4`](https://github.com/retrofor/iamai/commit/bae16f4025bfaa0c8296924865f232c0234699c5) - **readme**: update *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`281cf90`](https://github.com/retrofor/iamai/commit/281cf904379797b9fec74e9621d92fb751fce88a) - **project**: update readme.text *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`663a70f`](https://github.com/retrofor/iamai/commit/663a70ffb1bbdaaebc425629f53d49f073d2cf26) - **project**: bump version into 0.0.3b4 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`6565229`](https://github.com/retrofor/iamai/commit/65652292cf7de7f772e19f82eb502a68c986df28) - **project**: bump version to 0.0.3b5 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3b3] - 2024-02-22
### BREAKING CHANGES
- due to [`4e8a96f`](https://github.com/retrofor/iamai/commit/4e8a96f25665c08314d5e68e338327fa3f65e25a) - rename adapter "onebot11" -> "cqhttp" *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*:

  rename adapter "onebot11" -> "cqhttp"


### Bug Fixes
- [`23d0894`](https://github.com/retrofor/iamai/commit/23d0894c3edba5c88c55082a0dd345267a266c8a) - **readme**: format rst *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`22b40d0`](https://github.com/retrofor/iamai/commit/22b40d0af7e0b0255411f9cef749c3dbe95a3c7f) - **workflow**: build api for all packages *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`e366a34`](https://github.com/retrofor/iamai/commit/e366a34f270890e260c12eee4b96a9e85defd5f6) - remove `readme` key and add `long_description_content`. *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`5a1c0e2`](https://github.com/retrofor/iamai/commit/5a1c0e21094857bf8f997823b8067d27887d11e2) - **workflow**: resolve cp -r not specified error *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`0309a33`](https://github.com/retrofor/iamai/commit/0309a33d20634e00828d081dba53ff01a83bab45) - **workflow**: rename dir name *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`d191c0c`](https://github.com/retrofor/iamai/commit/d191c0ccbbebfe90d78659f05b3699a7562b3a49) - **project**: update url and readme file *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Refactors
- [`4e8a96f`](https://github.com/retrofor/iamai/commit/4e8a96f25665c08314d5e68e338327fa3f65e25a) - **adapter**: rename adapter "onebot11" -> "cqhttp" *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`283d1af`](https://github.com/retrofor/iamai/commit/283d1af748a1c309bd6c38b1aabf820e9b56d1e3) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`c7bda67`](https://github.com/retrofor/iamai/commit/c7bda6707669d21141f0af88a7dadfffa4b3783e) - **workflow**: update api build step *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`a69aff7`](https://github.com/retrofor/iamai/commit/a69aff74c1d3f967f9825910d2de13f2243517c7) - **docs**: update conf.py *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`b024674`](https://github.com/retrofor/iamai/commit/b0246747ddc95eced7a68a9f04f22ac2a8e6cf7f) - **docs**: change html title *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`607af84`](https://github.com/retrofor/iamai/commit/607af845fa41c4c9c9612512092494c399a896be) - optimize all comments *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`aa14246`](https://github.com/retrofor/iamai/commit/aa14246e0c44fe752d0e372bdbd9654008db45f3) - **docs**: update api docs with sphinx-apidoc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`22bfbed`](https://github.com/retrofor/iamai/commit/22bfbed1dc21384139ad527e8c689692a73e419f) - **workflow**: delete api dir *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`1216d89`](https://github.com/retrofor/iamai/commit/1216d89493fd259f4c3df8c9b55c1b956f17acf5) - **docs**: format changelog *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`a67637f`](https://github.com/retrofor/iamai/commit/a67637f2936aa0c19ae3b9f0a3b6712b70c9decd) - **docs**: fix file name *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`7172a20`](https://github.com/retrofor/iamai/commit/7172a204c218ec7da69a6504b6ac20c792b94f6a) - **adapter**: apscheduler adpater update deps *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`6d4ef4a`](https://github.com/retrofor/iamai/commit/6d4ef4a60e98ba66528e629eb0f9a76e072d0d24) - **packages**: update LICENSE *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3b2] - 2024-02-14
### Bug Fixes
- [`b8e1178`](https://github.com/retrofor/iamai/commit/b8e11784375b670293d4c4cc9f455a2c1c3a93dd) - change project readme file suffix *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`83adf17`](https://github.com/retrofor/iamai/commit/83adf171f47a7927c2f156d0c2aa37a2aca40f50) - bump version to 003b2 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3b1] - 2024-01-29
### Refactors
- [`1fa6516`](https://github.com/retrofor/iamai/commit/1fa6516950fc2c1a967154ea916c580efb352d39) - rename example to examples *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### Chores
- [`5d7f813`](https://github.com/retrofor/iamai/commit/5d7f81398bee5dd8926580e4f41baab35d0b38a4) - **docs**: update api docs *(PR [#273](https://github.com/retrofor/iamai/pull/273) by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`fe9b8cb`](https://github.com/retrofor/iamai/commit/fe9b8cbee74b1d470c6033550f99a9f6afbb8d2a) - **workflows**: disable useGitmojis *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`f5e26df`](https://github.com/retrofor/iamai/commit/f5e26df94e10254e55b9de7f632c069c10cc1433) - **workflows**: update api build steps *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`f222434`](https://github.com/retrofor/iamai/commit/f222434831b73f6a8a940498b670b45f33b96995) - **deps**: bump ncipollo/release-action from 1.12.0 to 1.13.0 *(PR [#275](https://github.com/retrofor/iamai/pull/275) by [@dependabot[bot]](https://github.com/apps/dependabot))*
- [`aa61cf1`](https://github.com/retrofor/iamai/commit/aa61cf10d711c33c14ae22c641a96c6deec19570) - **deps**: bump stefanzweifel/git-auto-commit-action from 4 to 5 *(PR [#274](https://github.com/retrofor/iamai/pull/274) by [@dependabot[bot]](https://github.com/apps/dependabot))*


## [v0.0.3a3] - 2024-01-28
### :wrench: Chores
- [`84be7fd`](https://github.com/retrofor/iamai/commit/84be7fdae9f828e9422d209a1919a6bdbec29ac2) - **workflows**: remove step copy credits *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`9732bf1`](https://github.com/retrofor/iamai/commit/9732bf1c8bc617e324c0b1f1b2500caf78ba79b1) - **version**: bump version from 0.0.3a2 to 0.0.3a3 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


## [v0.0.3a2] - 2024-01-28
### :boom: BREAKING CHANGES
- due to [`7f1ceea`](https://github.com/retrofor/iamai/commit/7f1ceea0763e6914a6d52b398ee9959f98470b52) - cancel building the credit with workflow *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*:

  cancel building the credit with workflow


### :bug: Bug Fixes
- [`ea0ada8`](https://github.com/retrofor/iamai/commit/ea0ada86ac23f805cd76b3e45d6971fed638468a) - **workflow**: rename changelog.md to CHANGELOG.md and replace the path *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### :recycle: Refactors
- [`59adea4`](https://github.com/retrofor/iamai/commit/59adea4e43ac2c2a20e44b7622ee9c05670b728b) - **example**: rename tests dir to examples dir *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*

### :wrench: Chores
- [`0428f79`](https://github.com/retrofor/iamai/commit/0428f79806188399cdd09f9cc459841228429923) - **workflow**: change regex pattern *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4651ea8`](https://github.com/retrofor/iamai/commit/4651ea8a81a449e4398a641664bb831bd6b7b518) - **workflow**: revoke changelog.md *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`a15ab94`](https://github.com/retrofor/iamai/commit/a15ab948c12ae5be9dc6d2133ec85b793927d6a4) - **deps**: remove sophia-doc *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`7f1ceea`](https://github.com/retrofor/iamai/commit/7f1ceea0763e6914a6d52b398ee9959f98470b52) - **credits**: cancel building the credit with workflow *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`6048e01`](https://github.com/retrofor/iamai/commit/6048e01a34ba795e2b98d46bb9a9d0421dcad377) - **workflows**: delete relese-drafter.yml *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`bba1a90`](https://github.com/retrofor/iamai/commit/bba1a902f63b8ce3208f588e19dd1f95b0d8e578) - update ignored files *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`4b3fadf`](https://github.com/retrofor/iamai/commit/4b3fadfcb09c8f6c41ab794e10e45ece535c9a98) - delete example/config.toml *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*
- [`b3679ba`](https://github.com/retrofor/iamai/commit/b3679ba5beabe4ea913dda4507b5e795dcc39c4d) - **version**: bump version 0.0.3a1 to 0.0.3a2 *(commit by [@HsiangNianian](https://github.com/HsiangNianian))*


[v0.0.3a2]: https://github.com/retrofor/iamai/compare/v0.0.3a1...v0.0.3a2
[v0.0.3a3]: https://github.com/retrofor/iamai/compare/v0.0.3a2...v0.0.3a3
[v0.0.3b1]: https://github.com/retrofor/iamai/compare/v0.0.3a3...v0.0.3b1
[v0.0.3b2]: https://github.com/retrofor/iamai/compare/v0.0.3b1...v0.0.3b2
[v0.0.3b3]: https://github.com/retrofor/iamai/compare/v0.0.3b2...v0.0.3b3
[v0.0.3b5]: https://github.com/retrofor/iamai/compare/v0.0.3b3...v0.0.3b5
[v0.0.3rc3]: https://github.com/retrofor/iamai/compare/v0.0.3rc1...v0.0.3rc3
[v0.0.3-rc.4]: https://github.com/retrofor/iamai/compare/v0.0.3rc3...v0.0.3-rc.4
[v0.0.4]: https://github.com/retrofor/iamai/compare/v0.0.3...v0.0.4
[v0.1.4]: https://github.com/retrofor/iamai/compare/v0.0.4...v0.1.4
[v0.1.6]: https://github.com/retrofor/iamai/compare/v0.1.5...v0.1.6
[v0.1.7]: https://github.com/retrofor/iamai/compare/v0.1.6...v0.1.7
[v0.1.8]: https://github.com/retrofor/iamai/compare/v0.1.7...v0.1.8
