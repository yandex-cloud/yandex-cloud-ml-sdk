from __future__ import annotations

from typing import Union

from yandex_cloud_ml_sdk._datasets.dataset import BaseDataset

#: Type alias for dataset inputs.
DatasetType = Union[str, BaseDataset]


def coerce_dataset_id(dataset: DatasetType) -> str:
    """
    Coerce dataset input to a dataset ID string.

    This function accepts either a BaseDataset object or a string and returns
    the dataset ID as a string. If a BaseDataset object is provided, it extracts
    the ID from the object. If a string is provided, it returns it as-is.

    :param dataset: The dataset to extract ID from. Can be either a BaseDataset
        object or a string containing the dataset ID.
    """
    if isinstance(dataset, BaseDataset):
        return dataset.id
    if isinstance(dataset, str):
        return dataset

    raise TypeError(
        'the dataset parameter must contain a Dataset object, either a string with the dataset ID.')
