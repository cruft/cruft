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
## 1.2.0 - 7 August 2020
- [Fixed issue #26](https://github.com/timothycrosley/cruft/issues/26): Support for Directory as there are multiple templates in single repo
- [Fixed issue #18 & #13](https://github.com/timothycrosley/cruft/issues/18): Commands fail with OSError randomly on windows

## 1.1.2 - 3 October 2019
- [Fixed Issue #3](https://github.com/timothycrosley/cruft/issues/3): Patch failed to apply.
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
