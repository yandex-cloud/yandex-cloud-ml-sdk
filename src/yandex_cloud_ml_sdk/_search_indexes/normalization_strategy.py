# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import enum

from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import NormalizationStrategy

from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase


class IndexNormalizationStrategy(ProtoEnumBase, enum.IntEnum):
    NORMALIZATION_STRATEGY_UNSPECIFIED = NormalizationStrategy.NORMALIZATION_STRATEGY_UNSPECIFIED
    MIN_MAX = NormalizationStrategy.MIN_MAX
    L2 = NormalizationStrategy.L2
