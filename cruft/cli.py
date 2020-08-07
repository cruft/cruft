"""This module defines CLI interaction when using `cruft`.

This is powered by [hug](https://github.com/hugapi/hug) which means unless necessary
it should maintain 1:1 compatibility with the programmatic API definition in the
[API module](/reference/cruft/api)

- `cruft create`: Expands the specified Cookiecutter template on disk.
- `cruft check`: Checks to see if the expanded template is up-to-date with latest version.
- `cruft update`: Attempts to updates an expanded Cookiecutter template to the latest version.
"""
import sys

import hug

from cruft import api, logo

hug_api = hug.API(__name__, doc=logo.ascii_art)


def _check_command_output(up_to_date: bool) -> None:
    if not up_to_date:
        print("")
        sys.exit(
            "FAILURE: Project's cruft is out of date! Run `cruft update` to clean this mess up."
        )
    else:
        print("")
        print("SUCCESS: Good work! Project's cruft is up to date and as clean as possible :).")


def _update_output(updated: bool) -> None:
    if not updated:
        print("")
        print("Nothing to do, project's cruft is already up to date!")
    else:
        print("")
        print("Good work! Project's cruft has been updated and is as clean as possible!")


def _link_output(linked: bool) -> None:
    if linked:
        print("")
        print("Project successfully linked to template!")
    else:
        print("")
        print("Project linking failed :(")


cli = hug.cli(api=hug_api)
cli(api.create)
cli.output(_update_output)(api.update)
cli.output(_check_command_output)(api.check)
cli.output(_link_output)(api.link)
