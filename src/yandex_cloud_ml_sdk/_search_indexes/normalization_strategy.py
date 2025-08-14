# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import enum

from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import NormalizationStrategy

from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase


class IndexNormalizationStrategy(ProtoEnumBase, enum.IntEnum):
    """
    Enumeration for index normalization strategies.

    This class defines the various normalization strategies that can be applied
    to an index.
    """
    #: indicates that no normalization strategy has been specified
    NORMALIZATION_STRATEGY_UNSPECIFIED = NormalizationStrategy.NORMALIZATION_STRATEGY_UNSPECIFIED
    #: represents the Min-Max normalization strategy
    MIN_MAX = NormalizationStrategy.MIN_MAX
    #: represents the L2 normalization strategy
    L2 = NormalizationStrategy.L2
