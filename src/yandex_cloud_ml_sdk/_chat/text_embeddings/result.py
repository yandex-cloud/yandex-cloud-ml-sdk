# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, overload

from yandex_cloud_ml_sdk._types.result import BaseJsonResult, SDKType
from yandex_cloud_ml_sdk._types.schemas import JsonObject
from yandex_cloud_ml_sdk._types.usage import BaseUsage


@dataclass(frozen=True)
class EmbeddingsUsage(BaseUsage):
    """
    A class representing usage statistics for chat embedding requests.
    """

    @property
    def prompt_tokens(self) -> int:
        """Alias for input_text_tokens for compatibility with chat naming."""
        return self.input_text_tokens


@dataclass(frozen=True)
class ChatEmbeddingsModelResult(BaseJsonResult, Sequence):
    """
    Represents the result of a text embeddings model.

    It holds the embedding vector, the number of tokens, and the
    version of the model that is used to generate embeggings.
    """

    #: the embedding vector as a tuple of floats
    embedding: tuple[float, ...]
    #: URI of the chat model used for generating the result
    model: str
    #: Usage statistics for the embedding request
    usage: EmbeddingsUsage | None

    @classmethod
    def _from_json(cls, *, data: JsonObject, sdk: SDKType) -> ChatEmbeddingsModelResult:
        model = data.get('model')
        assert isinstance(model, str)
        raw_data = data.get('data')
        assert isinstance(raw_data, list)
        assert len(raw_data) == 1
        first_data = raw_data[0]
        assert isinstance(first_data, dict)
        embedding = first_data.get('embedding')
        assert isinstance(embedding, list)

        usage: EmbeddingsUsage | None = None
        if usage_value := data.get('usage'):
            assert isinstance(usage_value, dict)
            raw_usage = cast(dict[str, int], usage_value)
            usage = EmbeddingsUsage(
                input_text_tokens=raw_usage['prompt_tokens'],
                total_tokens=raw_usage['total_tokens']
            )

        return cls(
            model=model,
            embedding=tuple(cast(list[float], embedding)),
            usage=usage
        )

    def __len__(self):
        return len(self.embedding)

    @overload
    def __getitem__(self, index: int, /) -> float:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[float, ...]:
        pass

    def __getitem__(self, index, /):
        return self.embedding[index]

    def __array__(self, dtype=None, copy=None):
        import numpy  # pylint: disable=import-outside-toplevel

        if copy is False:
            raise ValueError(
                "`copy=False` isn't supported. A copy is always created."
            )

        return numpy.array(self.embedding, dtype=dtype)
