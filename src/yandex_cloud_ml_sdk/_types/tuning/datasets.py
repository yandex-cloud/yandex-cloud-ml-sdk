from __future__ import annotations

from numbers import Number
from typing import Dict, Iterable, Tuple, Union

from yandex_cloud_ml_sdk._datasets.dataset import BaseDataset

DatasetType = Union[str, BaseDataset]
WeightedDatasetType = Tuple[DatasetType, float]
TuningDatasetType = Union[DatasetType, WeightedDatasetType]
TuningDatasetsType = Union[TuningDatasetType, Iterable[TuningDatasetType], Dict[DatasetType, float]]

ERROR_TEXT = ' '.join("""datasets must contain
string with dataset ID,
BaseDataset object,
tuple ("id", float)),
tuple (BaseDataset, float),
either any Iterable containing any value of above types,
got {}
""".split('\n'))

def coerce_datasets(datasets: TuningDatasetsType) -> tuple[tuple[str, float], ...]:
    if (
        isinstance(datasets, (str, BaseDataset)) or
        isinstance(datasets, tuple) and len(datasets) == 2 and isinstance(datasets[1], Number)
    ):
        datasets = [datasets]
    elif isinstance(datasets, dict):
        datasets = tuple(datasets.items())
    elif not isinstance(datasets, Iterable):
        raise TypeError(ERROR_TEXT.format(datasets))

    coerced = []

    for dataset in datasets:
        if isinstance(dataset, str):
            coerced.append((dataset, 1.0))
        elif isinstance(dataset, BaseDataset):
            coerced.append((dataset.id, 1.0))
        elif isinstance(dataset, tuple) and len(dataset) == 2:
            id_, weight = dataset
            if isinstance(id_, BaseDataset):
                id_ = id_.id

            if not isinstance(id_, str) or not isinstance(weight, Number):
                raise TypeError(ERROR_TEXT.format(dataset))

            coerced.append((id_, float(weight)))
        else:
            raise TypeError(ERROR_TEXT.format(dataset))

    return tuple(coerced)
