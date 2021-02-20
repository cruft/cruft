from functools import wraps

from . import cookiecutter, cruft, diff, generate, iohelper

try:
    from examples import example
except ImportError:  # pragma: no cover
    # In case examples is not available,
    # we introduce a no-op decorator.
    def example(*_args, **_kwargs):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapper

        return decorator


__all__ = ["cookiecutter", "cruft", "diff", "example", "generate", "iohelper"]
