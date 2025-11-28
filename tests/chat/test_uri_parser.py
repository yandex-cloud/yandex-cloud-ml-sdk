import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML

pytestmark = pytest.mark.asyncio

async def test_run(folder_id, auth):
    cls = AsyncYCloudML(
        folder_id=folder_id,
        auth='y0__xC2o6HJARjB3RMg0JS96BQwoJmuhQjEqZBq6zns0GqMJ9OskUPXPnguZA'
    )
    print(auth)
    print(folder_id)
    res = await cls.chat.completions.list()
    print(res)