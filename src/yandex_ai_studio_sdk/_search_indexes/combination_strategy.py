# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
import enum
from collections.abc import Collection
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import CombinationStrategy as ProtoCombinationStrategy
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import MeanCombinationStrategy as ProtoMeanCombinationStrategy
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import (
    ReciprocalRankFusionCombinationStrategy as ProtoReciprocalRankFusionCombinationStrategy
)

from yandex_ai_studio_sdk._utils.proto import ProtoEnumBase

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._sdk import BaseSDK


class BaseIndexCombinationStrategy(abc.ABC):
    """A class for index combination strategies."""
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto: Any, sdk: BaseSDK) -> BaseIndexCombinationStrategy:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoCombinationStrategy:
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoCombinationStrategy, sdk: BaseSDK) -> BaseIndexCombinationStrategy:
        if proto.HasField('mean_combination'):
            return MeanIndexCombinationStrategy._from_proto(
                proto=proto.mean_combination,
                sdk=sdk
            )
        if proto.HasField('rrf_combination'):
            return ReciprocalRankFusionIndexCombinationStrategy._from_proto(
                proto=proto.rrf_combination,
                sdk=sdk
            )
        raise NotImplementedError(
            'combination strategies other then Mean and RRF are not supported in this SDK version'
        )

_orig = ProtoMeanCombinationStrategy.MeanEvaluationTechnique

class MeanIndexEvaluationTechnique(ProtoEnumBase, enum.IntEnum):
    """A class with enumeration for mean index evaluation techniques."""
    #: an unspecified mean evaluation technique
    MEAN_EVALUATION_TECHNIQUE_UNSPECIFIED = _orig.MEAN_EVALUATION_TECHNIQUE_UNSPECIFIED
    #: the arithmetic mean, calculated as the sum of values divided by the count of values
    ARITHMETIC = _orig.ARITHMETIC
    #: the geometric mean, calculated as the n-th root of the product of n values
    GEOMETRIC = _orig.GEOMETRIC
    #: the harmonic mean, calculated as the reciprocal of the arithmetic mean of the reciprocals of the values
    HARMONIC = _orig.HARMONIC


@dataclass(frozen=True)
class MeanIndexCombinationStrategy(BaseIndexCombinationStrategy):
    """A class which contains mean index combination strategy with evaluation technique and weights."""
    #: the technique used for mean evaluation
    mean_evaluation_technique: MeanIndexEvaluationTechnique | None
    #: the weights associated with the evaluation technique
    weights: Collection[float] | None

    @classmethod
    # pylint: disable=unused-argument
    def _from_proto(cls, proto: ProtoMeanCombinationStrategy, sdk: BaseSDK) -> MeanIndexCombinationStrategy:
        return cls(
            mean_evaluation_technique=MeanIndexEvaluationTechnique._coerce(proto.mean_evaluation_technique),
            weights=tuple(proto.weights)
        )

    def _to_proto(self) -> ProtoCombinationStrategy:
        kwargs: dict[str, Any] = {}
        if self.mean_evaluation_technique:
            kwargs['mean_evaluation_technique'] = int(self.mean_evaluation_technique)
        if self.weights is not None:
            kwargs['weights'] = tuple(self.weights)

        return ProtoCombinationStrategy(
            mean_combination=ProtoMeanCombinationStrategy(**kwargs)
        )


@dataclass(frozen=True)
class ReciprocalRankFusionIndexCombinationStrategy(BaseIndexCombinationStrategy):
    """A class which describes reciprocal rank fusion index combination strategy. Reciprocal rank fusion is a method for combining multiple result sets with different relevance indicators into a single result set."""
    #: the parameter k for RRFscore. Default is 60.
    k: int | None = None

    @classmethod
    # pylint: disable=unused-argument
    def _from_proto(
        cls, proto: ProtoReciprocalRankFusionCombinationStrategy, sdk: BaseSDK
    ) -> ReciprocalRankFusionIndexCombinationStrategy:
        kwargs = {}
        if proto.HasField('k'):
            kwargs['k'] = proto.k.value
        return ReciprocalRankFusionIndexCombinationStrategy(
            **kwargs
        )

    def _to_proto(self) -> ProtoCombinationStrategy:
        kwargs = {}
        if self.k is not None:
            kwargs['k'] = Int64Value(value=self.k)
        return ProtoCombinationStrategy(
            rrf_combination=ProtoReciprocalRankFusionCombinationStrategy(**kwargs)
        )
