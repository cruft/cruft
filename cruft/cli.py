"""This module defines CLI interaction when using `cruft`.

This is powered by [hug](https://github.com/hugapi/hug) which means unless necessary
it should maintain 1:1 compatibility with the programmatic API definition in the
[API module](/reference/cruft/api)

- `cruft create`: Expands the specified Cookiecutter template on disk.
- `cruft update`: Attempts to updates an expanded Cookiecutter template to the latest version.
"""
import hug

from cruft import api, logo

cli = hug.cli(api=hug.API(__name__, doc=logo.ascii_art))
cli(api.create)

