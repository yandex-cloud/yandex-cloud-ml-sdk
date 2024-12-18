# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Collection

from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import CombinationStrategy as ProtoCombinationStrategy
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import MeanCombinationStrategy as ProtoMeanCombinationStrategy
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import (
    ReciprocalRankFusionCombinationStrategy as ProtoReciprocalRankFusionCombinationStrategy
)

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseIndexCombinationStrategy(abc.ABC):
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

class MeanIndexEvaluationTechnique(enum.IntEnum):
    MEAN_EVALUATION_TECHNIQUE_UNSPECIFIED = _orig.MEAN_EVALUATION_TECHNIQUE_UNSPECIFIED
    ARITHMETIC = _orig.ARITHMETIC
    GEOMETRIC = _orig.GEOMETRIC
    HARMONIC = _orig.HARMONIC

    @classmethod
    def _coerce(cls, technique: str | int ) -> MeanIndexEvaluationTechnique:
        if isinstance(technique, str):
            technique = _orig.Value(technique.upper())
        return cls(technique)


@dataclass(frozen=True)
class MeanIndexCombinationStrategy(BaseIndexCombinationStrategy):
    mean_evaluation_technique: MeanIndexEvaluationTechnique | None
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
            kwargs['weghts'] = tuple(self.weights)

        return ProtoCombinationStrategy(
            mean_combination=ProtoMeanCombinationStrategy(**kwargs)
        )


@dataclass(frozen=True)
class ReciprocalRankFusionIndexCombinationStrategy(BaseIndexCombinationStrategy):
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
