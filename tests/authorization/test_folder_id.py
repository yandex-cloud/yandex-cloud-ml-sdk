from __future__ import annotations

import pytest
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML

@pytest.mark.parametrize("sdk_class", [YCloudML, AsyncYCloudML])
def test_folder_id_from_env(monkeypatch, sdk_class, auth, interceptors, retry_policy):
    monkeypatch.setenv("YC_FOLDER_ID", "test-folder-id")
    sdk = sdk_class(
        auth=auth,
        interceptors=interceptors,
        retry_policy=retry_policy
    )
    assert sdk._folder_id == "test-folder-id"

@pytest.mark.parametrize("sdk_class", [YCloudML, AsyncYCloudML])
def test_folder_id_missing_raises_error(sdk_class, auth, interceptors, retry_policy):
    with pytest.raises(ValueError) as exc_info:
        sdk = sdk_class(
            auth=auth,
            interceptors=interceptors,
            retry_policy=retry_policy
        )
    assert "You must provide the 'folder_id' parameter or set the 'YC_FOLDER_ID' environment variable." in str(
        exc_info.value)