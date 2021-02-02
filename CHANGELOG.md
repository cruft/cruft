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
