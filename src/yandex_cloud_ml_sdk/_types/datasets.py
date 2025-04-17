from __future__ import annotations

from typing import Union

from yandex_cloud_ml_sdk._datasets.dataset import BaseDataset

DatasetType = Union[str, BaseDataset]


def coerce_dataset_id(dataset: DatasetType) -> str:
    if isinstance(dataset, BaseDataset):
        return dataset.id
    if isinstance(dataset, str):
        return dataset

    raise TypeError(
        'the dataset parameter must contain a Dataset object, either a string with the dataset ID.')
