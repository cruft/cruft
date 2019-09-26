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
## 1.1.1 - 25 September 2019
- Added optional support for reading skip options from `pyproject.toml`.

## 1.1.0 - 24 September 2019
- Added `link` command to link existing repositories to the Cookiecutter template that created them.
- Added `skip` option to `.cruft.json` file allowing template updates to be skipped per a repository.
- Improved patch applying from template updates.
- Added an interactive option on the `update` command to skip an individual update, while marking a repository as up-to-date.

## 1.0.0 - 23 September 2019
- Initial API stable release.
