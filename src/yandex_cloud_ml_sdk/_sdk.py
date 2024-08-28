from __future__ import annotations

import asyncio
import inspect
import os
import threading
from typing import Optional, Sequence

from get_annotations import get_annotations
from grpc import aio

from ._auth import BaseAuth
from ._client import AsyncCloudClient
from ._models import AsyncModels, Models
from ._retry import RetryPolicy
from ._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from ._types.resource import BaseResource


class BaseSDK:
    def __init__(
        self,
        *,
        folder_id: str,
        endpoint: UndefinedOr[str] = UNDEFINED,
        auth: UndefinedOr[str | BaseAuth] = UNDEFINED,
        retry_policy: UndefinedOr[RetryPolicy] = UNDEFINED,
        yc_profile: UndefinedOr[str] = UNDEFINED,
        service_map: UndefinedOr[dict[str, str]] = UNDEFINED,
        interceptors: UndefinedOr[Sequence[aio.ClientInterceptor]] = UNDEFINED,
    ):
        """
        Construct a new asynchronous sdk instance.

        :param folder_id: Yandex Cloud folder identifier which will be billed
           for models usage.
        :type folder_id: str
        :param endpoint: domain:port pair for Yandex Cloud API or any other
            grpc compatible target.
        :type endpoint: str
        :param auth: string with API Key, IAM token or one of yandex_cloud_ml_sdk.auth objects;
            in case of default Undefined value, there will be a mechanism to get token
            from environment
        :type api_key | BaseAuth: str
        :param service_map: a way to redefine endpoints for one or more cloud subservices
            with a format of dict {service_name: service_address}.
        :type service_map: Dict[str, str]

        """
        endpoint = self._get_endpoint(endpoint)
        retry_policy = retry_policy if is_defined(retry_policy) else RetryPolicy()

        self._client = AsyncCloudClient(
            endpoint=endpoint,
            auth=get_defined_value(auth, None),
            service_map=get_defined_value(service_map, {}),
            retry_policy=retry_policy,
            interceptors=get_defined_value(interceptors, None),
            yc_profile=get_defined_value(yc_profile, None),
        )
        self._folder_id = folder_id

        self._init_resources()

    def _init_resources(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member in members.items():
            if inspect.isclass(member) and issubclass(member, BaseResource):
                resource = member(name=member_name, sdk=self)
                setattr(self, member_name, resource)

    def _get_endpoint(self, endpoint: UndefinedOr[str]) -> str:
        if is_defined(endpoint):
            return endpoint

        if env_endpoint := os.getenv('YC_API_ENDPOINT'):
            return env_endpoint

        return 'api.cloud.yandex.net:443'

    # NB: All typehints on these classes must be 3.8-compatible
    # to properly work with get_annotations
    _event_loop: Optional[asyncio.AbstractEventLoop] = None
    _loop_thread: Optional[threading.Thread] = None
    _number: int = 0
    _lock = threading.Lock()

    @classmethod
    def _start_event_loop(cls):
        loop = cls._event_loop
        asyncio.set_event_loop(loop)
        loop.run_forever()

    @staticmethod
    def _get_event_loop() -> asyncio.AbstractEventLoop:
        """This event loop is used at yandex_cloud_ml_sdk._utils.sync.run_sync
        for synchronized run of async functions.

        NB that loop must be kinda a singleton, because grpc.aio.* things
        are breaking when you try to use it at different event loops with different
        threads.
        """
        # pylint: disable=protected-access

        # it was a class method first, but it breaked when test with
        # both AsyncSDK and SDK appeared
        kls = BaseSDK

        if kls._event_loop is not None:
            return kls._event_loop

        with kls._lock:
            if kls._event_loop is None:
                thread_name = f'{kls.__name__}-{kls._number}'
                kls._number += 1

                kls._event_loop = asyncio.new_event_loop()
                kls._loop_thread = threading.Thread(
                    target=kls._start_event_loop,
                    daemon=True,
                    name=thread_name
                )
                kls._loop_thread.start()

        return kls._event_loop


class AsyncYCloudML(BaseSDK):
    models: AsyncModels


class YCloudML(BaseSDK):
    models: Models
