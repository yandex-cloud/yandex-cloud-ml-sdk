# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import enum

from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import NormalizationStrategy


class IndexNormalizationStrategy(enum.IntEnum):
    NORMALIZATION_STRATEGY_UNSPECIFIED = NormalizationStrategy.NORMALIZATION_STRATEGY_UNSPECIFIED
    MIN_MAX = NormalizationStrategy.MIN_MAX
    L2 = NormalizationStrategy.L2

    @classmethod
    def _coerce(cls, strategy: str | int | IndexNormalizationStrategy) -> IndexNormalizationStrategy:
        if isinstance(strategy, str):
            strategy = NormalizationStrategy.Value(strategy.upper())
        return cls(strategy)
