"""**cruft**

Allows you to maintain all the necessary cruft for packaging and building projects separate from
the code you intentionally write. Built on-top of, and fully compatible with, CookieCutter.
"""
from cruft._commands import check, create, diff, link, update
from cruft._version import __version__

__all__ = ["create", "check", "diff", "update", "link", "__version__"]
