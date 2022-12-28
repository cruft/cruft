Install the latest
===================

To install the latest version of cruft simply run:

`pip3 install cruft`

OR

`poetry add cruft`

OR

`pipenv install cruft`


Changelog
=========

## 2.12.0 - 28 December 2022
- Uncapped version requirements (including Python) for greater compatiblity
- [Fixed issue #166](https://github.com/cruft/cruft/issues/166): Fixed compatiblity with latest version of cookiecutter
- [Implemented #184](https://github.com/cruft/cruft/issues/184): Store checkout parameter when using link command
- Improvements to update command

## 2.11.1 - 28 August 2022
- [Fixed issue #177](https://github.com/cruft/cruft/issues/177): cruft update can't apply diffs when git's diff.mnemonicprefix config is set

## 2.11.0 - 29 July 2022
- [Fixed issue #168](https://github.com/cruft/cruft/issues/168): Add support for typer v0.6+
- [Fixed issue #162](https://github.com/cruft/cruft/issues/162): Add support for cookiecutter v2

## 2.10.2 - 20 Apr 2022
- [Fixed issue #152](https://github.com/cruft/cruft/issues/152): Upgrade version of importlib-metadata

## 2.10.1 - 8 Nov 2021
- Fixed missing dependency on importlib-metadata

## 2.10.0 - 7 Nov 2021
- [Fixed issue #41](https://github.com/cruft/cruft/issues/41): Add windows support
- [Fixed issue #112](https://github.com/cruft/cruft/issues/112): Add support for generating the project with always skipped files on update
- [Fixed issue #123](https://github.com/cruft/cruft/issues/123): Feature request: Faster implementation for cruft check
- [Fixed issue #124](https://github.com/cruft/cruft/issues/124): cruft 2.9.0 on Pypi requires click <= 8.0.0
- [Fixed issue #131](https://github.com/cruft/cruft/issues/131): Feature request: support binary files patching

## 2.9.0 - 30 June 2021
- [Fixed issue #64](https://github.com/cruft/cruft/issues/64): Feature request: support globs for skipped files
- [Fixed issue #101](https://github.com/cruft/cruft/issues/101): Update error if symlink is present in project
- [Fixed issue #81](https://github.com/cruft/cruft/issues/81): cruft update leads to UnicodeDecodeError
- [Fixed issue #115](https://github.com/cruft/cruft/issues/115): Warn when pyproject.toml exists but cannot be read

## 2.8.0 - 9 March 2021
- [Fixed issue #68](https://github.com/cruft/cruft/issues/68): Add support for cruft create/update in a sub directory in an existing repository
- [Fixed issue #91](https://github.com/cruft/cruft/issues/91): Support Updating When Repo has Untracked Files

## 2.7.0 - 22 February 2021
- [Fixed issue #76](https://github.com/cruft/cruft/issues/76): diff.noprefix=yes breaks tests
- [Fixed issue #92](https://github.com/cruft/cruft/issues/92): Store checkout value in cruft state

## 2.6.1 - 1 February 2021
- [Fixed issue #82](https://github.com/cruft/cruft/issues/82): error: git diff header lacks filename information when removing 1 leading pathname component

## 2.6.0 - 7 November 2020
- [Fixed issue #53](https://github.com/cruft/cruft/issues/53): Update fails on moved files, without clear error messages
- [Fixed issue #67](https://github.com/cruft/cruft/issues/67): Update fails on new files
- [Fixed issue #71](https://github.com/cruft/cruft/issues/71): Fix the order for cruft diff

## 2.5.0 - 1 October 2020
- [Fixed issue #58](https://github.com/cruft/cruft/issues/58): Add a diff command that compares the current project to the upstream cookiecutter

## 2.4.0 - 18 September 2020
- [Fixed issue #52](https://github.com/cruft/cruft/issues/52): Clarify error message when specified commit is missing from repo
- [Fixed issue #55](https://github.com/cruft/cruft/issues/55): Add support for ssh connections to template repository
- [Fixed issue #56](https://github.com/cruft/cruft/issues/56): Improve error message when providing incorrect credentials

## 2.3.0 - 16 August 2020
- [Fixed issue #46](https://github.com/cruft/cruft/issues/46): Cruft update fails to apply without providing conflits to resolve manually

## 2.2.0 - 16 August 2020
- [Fixed issue #44](https://github.com/cruft/cruft/issues/44): Cruft update can drop changes

## 2.1.0 - 13 August 2020
- [Fixed issue #42](https://github.com/cruft/cruft/issues/42): Cruft check fails if the current version of the project is ahead of the cookiecutter

## 2.0.0 - 12 August 2020
- [Implemented #31](https://github.com/cruft/cruft/issues/31): Moved from hug -> typer and refactored Python API.
- [Implemented #39](https://github.com/cruft/cruft/issues/39): Simplify internals by fully droping Windows support beyond WSL.
- [Fixed issue #7](https://github.com/cruft/cruft/issues/7): Incorrect CLI help documentation.
- [Fixed issue #23](https://github.com/cruft/cruft/issues/23): Relative paths not supported.

## 1.4.0 - 11 August 2020
- [Fixed issue #21](https://github.com/cruft/cruft/issues/21): Improve messaging when diff is empty.
- [Implemented #15](https://github.com/cruft/cruft/issues/15): Allow piping diff to an external utility.
- [Implemented #33](https://github.com/cruft/cruft/issues/24): When possible, use git apply instead of `patch` .

## 1.3.0 - 9 August 2020
- [Fixed issue #8](https://github.com/cruft/cruft/issues/8): Fall back to no-backup if patch doesn't support --merge.
- [Fixed issue #11](https://github.com/cruft/cruft/issues/11): Config file flag --config_file broken.
- [Implemented #24](https://github.com/cruft/cruft/issues/24): Allow `cruft update` to specify a branch of the cookiecutter repo.
- [Implemented #10](https://github.com/cruft/cruft/issues/10): Provide a mechanism to choose template version.

Internal:
- Refactored `api` module into a collection of smaller better scoped modules.

## 1.2.0 - 7 August 2020
- [Fixed issue #26](https://github.com/cruft/cruft/issues/26): Support for Directory as there are multiple templates in single repo
- [Fixed issue #18 & #13](https://github.com/cruft/cruft/issues/18): Commands fail with OSError randomly on windows

## 1.1.2 - 3 October 2019
- [Fixed Issue #3](https://github.com/cruft/cruft/issues/3): Patch failed to apply.
- Updated to use pathlib.
- Improved `pyproject.toml` skip_files, avoiding duplication into `.cruft.json` file.

## 1.1.1 - 25 September 2019
- Added optional support for reading skip options from `pyproject.toml`.

## 1.1.0 - 24 September 2019
- Added `link` command to link existing repositories to the Cookiecutter template that created them.
- Added `skip` option to `.cruft.json` file allowing template updates to be skipped per a repository.
- Improved patch applying from template updates.
- Added an interactive option on the `update` command to skip an individual update, while marking a repository as up-to-date.

## 1.0.0 - 23 September 2019
- Initial API stable release.
