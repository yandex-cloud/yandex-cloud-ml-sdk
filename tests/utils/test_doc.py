from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk._utils.doc import doc_from


def test_doc_from_class() -> None:
    class A:
        """A doc"""

    @doc_from(A)
    class B:
        def b(self):
            return 1

    assert B.__doc__ == 'A doc'
    assert B().b() == 1


def test_doc_from_method() -> None:
    class A:
        def a(self):
            """a doc"""

    class B:
        @doc_from(A.a)
        def b(self):
            return 1

    assert B.b.__doc__ == 'a doc'
    assert B().b() == 1


def test_doc_format() -> None:
    class A:
        """A doc {placeholder}"""

    @doc_from(A, placeholder="B")
    class B:
        def b(self):
            return 1

    assert B.__doc__ == 'A doc B'


def test_doc_wrong_types() -> None:
    class A:
        """A doc"""

    with pytest.raises(AssertionError):
        @doc_from(A)
        class B:
            """B doc"""

        assert B  # type: ignore[truthy-function]

    class A2:
        """A2 doc {placeholder}"""

    with pytest.raises(KeyError):
        @doc_from(A2, place="B")
        class B3:
            pass

        assert B3  # type: ignore[truthy-function]
