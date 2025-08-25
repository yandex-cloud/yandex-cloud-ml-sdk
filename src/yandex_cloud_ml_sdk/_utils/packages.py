from __future__ import annotations

import functools
import importlib.metadata
import inspect
import types
from typing import Callable, TypeVar

import packaging.specifiers
import packaging.version
from typing_extensions import ParamSpec

P = ParamSpec('P')
R = TypeVar('R')


def requires_package(
    package_name: str, requirements: str, method_name: str
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to ensure a package with specific version requirements is installed.

    This decorator checks if the specified package is installed and meets the version
    requirements before allowing the decorated method to execute. If the package is
    not installed or doesn't meet the version requirements, a RuntimeError is raised.

    Args:
        package_name (str): The name of the required package.
        requirements (str): Version requirements specification (e.g., ">=1.0.0", "~=2.1").
        method_name (str): Name of the method being decorated (used in error messages).
    """
    required_versions = packaging.specifiers.SpecifierSet(requirements)

    def decorator(method: Callable[P, R]) -> Callable[P, R]:
        """
        Inner decorator function that wraps the target method.

        Args:
            method (Callable[P, R]): The method to be decorated.
        """
        @functools.wraps(method)
        def function(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            Wrapper function that performs package checking before method execution.

            Args:
                *args (P.args): Positional arguments for the wrapped method.
                **kwargs (P.kwargs): Keyword arguments for the wrapped method.
            """
            error: str | None = None
            try:
                package_version = importlib.metadata.version(package_name)
                installed_version = packaging.version.parse(package_version)

                if installed_version not in required_versions:
                    error = f', but you have "{installed_version}" installed'
            except importlib.metadata.PackageNotFoundError:
                error = ", but you don't have any version installed"
            if error is not None:
                e = RuntimeError(
                    f'"{method_name}" requires package "{package_name}{requirements}" to be installed{error}'
                )
                current_frame = inspect.currentframe()
                new_tb: types.TracebackType | None = None
                if current_frame and current_frame.f_back:
                    caller_frame = current_frame.f_back
                    new_tb = types.TracebackType(
                        tb_next=None,
                        tb_frame=caller_frame,
                        tb_lasti=caller_frame.f_lasti,
                        tb_lineno=caller_frame.f_lineno,
                    )
                raise e.with_traceback(new_tb)

            return method(*args, **kwargs)
        return function
    return decorator
