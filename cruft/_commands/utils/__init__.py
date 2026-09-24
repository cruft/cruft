from functools import wraps

from . import cookiecutter, cruft, diff, generate, iohelper

try:
    from examples import example
except Exception:  # pragma: no cover
    # examples may be missing, or another package may own the top-level
    # ``examples`` name and raise on import (see #339).
    def example(*_args, **_kwargs):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapper

        return decorator


__all__ = ["cookiecutter", "cruft", "diff", "example", "generate", "iohelper"]
