import pytest

from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML  # type: ignore


def test_folder_id_from_env(monkeypatch, auth, interceptors, retry_policy, test_client_maker):
    monkeypatch.setenv("YC_FOLDER_ID", "test-folder-id")
    sdk = YCloudML(
        auth=auth,
        interceptors=interceptors,
        retry_policy=retry_policy
    )
    if test_client_maker:
        sdk._client = test_client_maker()
    assert sdk._folder_id == "test-folder-id"


def test_async_folder_id_from_env(monkeypatch, auth, interceptors, retry_policy, test_client):
    monkeypatch.setenv("YC_FOLDER_ID", "test-folder-id")
    sdk = AsyncYCloudML(
        auth=auth,
        interceptors=interceptors,
        retry_policy=retry_policy
    )
    if test_client:
        sdk._client = test_client
    assert sdk._folder_id == "test-folder-id"


def test_folder_id_missing_raises_error(auth, interceptors, retry_policy, test_client_maker):
    with pytest.raises(ValueError) as exc_info:
        sdk = YCloudML(
            auth=auth,
            interceptors=interceptors,
            retry_policy=retry_policy
        )
        if test_client_maker:
            sdk._client = test_client_maker()

    assert "You must provide the 'folder_id' parameter or set the 'YC_FOLDER_ID' environment variable." in str(
        exc_info.value)


def test_async_folder_id_missing_raises_error(auth, interceptors, retry_policy, test_client):
    with pytest.raises(ValueError) as exc_info:
        sdk = AsyncYCloudML(
            auth=auth,
            interceptors=interceptors,
            retry_policy=retry_policy
        )
        if test_client:
            sdk._client = test_client

    assert "You must provide the 'folder_id' parameter or set the 'YC_FOLDER_ID' environment variable." in str(
        exc_info.value)
