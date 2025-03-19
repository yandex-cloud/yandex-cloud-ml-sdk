from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, cast

# pylint: disable=no-name-in-module
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import TextEmbeddingPairParams, TextEmbeddingTripletParams

from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams

EmbeddingsTuneType = Literal['pair', 'triplet']
ProtoParamsName = Literal['text_embedding_pair_params', 'text_embedding_triplet_params']


@dataclass(frozen=True)
class TextEmbeddingsModelTuneParams(BaseTuningParams):
    @property
    def _proto_tuning_params_type(
        self
    ) -> type[TextEmbeddingPairParams] | type[TextEmbeddingTripletParams]:
        assert self.embeddings_tune_type
        return {
            'pair': TextEmbeddingPairParams,
            'triplet': TextEmbeddingTripletParams,
        }[self.embeddings_tune_type]

    @property
    def _proto_tuning_argument_name(self) -> ProtoParamsName:
        assert self.embeddings_tune_type
        result = {
            'pair': 'text_embedding_pair_params',
            'triplet': 'text_embedding_triplet_params',
        }[self.embeddings_tune_type]
        return cast(ProtoParamsName, result)

    @property
    def _ignored_fields(self):
        return super()._ignored_fields + ('embeddings_tune_type', )

    def __post_init__(self):
        if self.embeddings_tune_type not in ('pair', 'triplet'):
            raise ValueError(
                f'embeddings_tune_type must be {EmbeddingsTuneType}, got {self.embeddings_tune_type}'
            )

        if self.dimensions and not isinstance(self.dimensions, Sequence):
            raise ValueError(f'dimensions must be Sequence: tuple, list, etc, not {type(self.dimensions)}')

    def _asdict(self) -> dict:
        result = super()._asdict()
        dims = result.pop('dimensions', None)
        if dims is not None:
            # proto-compatible
            result['embedding_dims'] = tuple(dims)
        return result

    embeddings_tune_type: EmbeddingsTuneType | None = None
    seed: int | None = None
    lr: float | None = None
    n_samples: int | None = None
    additional_arguments: str | None = None
    dimensions: Sequence[int] | None = None
