from __future__ import annotations

import asyncio
import inspect
import os
import threading
from typing import Optional, Sequence

from get_annotations import get_annotations
from grpc import ChannelCredentials, aio

from ._assistants.domain import Assistants, AsyncAssistants, BaseAssistants
from ._auth import BaseAuth
from ._client import AsyncCloudClient
from ._datasets.domain import AsyncDatasets, BaseDatasets, Datasets
from ._files.domain import AsyncFiles, BaseFiles, Files
from ._messages.domain import AsyncMessages, BaseMessages, Messages
from ._models import AsyncModels, BaseModels, Models
from ._retry import RetryPolicy
from ._runs.domain import AsyncRuns, BaseRuns, Runs
from ._search_indexes.domain import AsyncSearchIndexes, BaseSearchIndexes, SearchIndexes
from ._threads.domain import AsyncThreads, BaseThreads, Threads
from ._tools.domain import Tools
from ._tuning.domain import AsyncTuning, BaseTuning, Tuning
from ._types.domain import BaseDomain
from ._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined


class BaseSDK:
    tools: Tools
    models: BaseModels
    threads: BaseThreads
    files: BaseFiles
    assistants: BaseAssistants
    runs: BaseRuns
    search_indexes: BaseSearchIndexes
    datasets: BaseDatasets
    tuning: BaseTuning

    _messages: BaseMessages

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
        enable_server_data_logging: UndefinedOr[bool] = UNDEFINED,
        grpc_credentials: UndefinedOr[ChannelCredentials] = UNDEFINED,
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
        :param enable_server_data_logging: when passed bool, we will add
            `x-data-logging-enabled: <value>` to all of requests, which will
            enable or disable logging of user data on server side.
            It will do something only on those parts of backends which supports
            this option.

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
            enable_server_data_logging=get_defined_value(enable_server_data_logging, None),
            credentials=get_defined_value(grpc_credentials, None),
        )
        self._folder_id = folder_id

        self._init_domains()

    def _init_domains(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member in members.items():
            if inspect.isclass(member) and issubclass(member, BaseDomain):
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
    tools: Tools
    models: AsyncModels
    files: AsyncFiles
    threads: AsyncThreads
    assistants: AsyncAssistants
    runs: AsyncRuns
    search_indexes: AsyncSearchIndexes
    datasets: AsyncDatasets
    tuning: AsyncTuning
    _messages: AsyncMessages


class YCloudML(BaseSDK):
    tools: Tools
    models: Models
    files: Files
    threads: Threads
    assistants: Assistants
    runs: Runs
    search_indexes: SearchIndexes
    datasets: Datasets
    tuning: Tuning
    _messages: Messages
