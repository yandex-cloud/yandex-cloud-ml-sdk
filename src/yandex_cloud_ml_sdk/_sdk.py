from __future__ import annotations

import asyncio
import inspect
import os
import threading
from typing import Sequence

from get_annotations import get_annotations
from grpc import aio
from typing_extensions import Self

from yandex_cloud_ml_sdk._utils.doc import doc_from

from ._assistants.domain import Assistants, AsyncAssistants, BaseAssistants
from ._auth import BaseAuth
from ._client import AsyncCloudClient
from ._datasets.domain import AsyncDatasets, BaseDatasets, Datasets
from ._files.domain import AsyncFiles, BaseFiles, Files
from ._logging import DEFAULT_DATE_FORMAT, DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL, LogLevel, setup_default_logging
from ._messages.domain import AsyncMessages, BaseMessages, Messages
from ._models import AsyncModels, BaseModels, Models
from ._retry import RetryPolicy
from ._runs.domain import AsyncRuns, BaseRuns, Runs
from ._search_api.domain import AsyncSearchAPIDomain, BaseSearchAPIDomain, SearchAPIDomain
from ._search_indexes.domain import AsyncSearchIndexes, BaseSearchIndexes, SearchIndexes
from ._threads.domain import AsyncThreads, BaseThreads, Threads
from ._tools.domain import AsyncTools, BaseTools, Tools
from ._tuning.domain import AsyncTuning, BaseTuning, Tuning
from ._types.domain import BaseDomain
from ._types.misc import UNDEFINED, PathLike, UndefinedOr, get_defined_value, is_defined


class BaseSDK:
    """The main class that needs to be instantiated to work with SDK."""
    tools: BaseTools
    models: BaseModels
    threads: BaseThreads
    files: BaseFiles
    assistants: BaseAssistants
    runs: BaseRuns
    #: API for `Yandex Search API <https://yandex.cloud/docs/search-api>`
    search_api: BaseSearchAPIDomain
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
        verify: UndefinedOr[bool | PathLike] = UNDEFINED,
    ):
        """Construct a new asynchronous sdk instance.

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
        :param verify: SSL certificates (a.k.a CA bundle) used to verify the identity
            of requested hosts. Either `True` (default CA bundle), a path to an SSL certificate file, or `False`
            (which will disable verification).
        :type verify: bool | pathlib.Path | str | os.PathLike
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
            verify=get_defined_value(verify, None),
        )
        self._folder_id = folder_id

        self._init_domains()

    def setup_default_logging(
        self,
        log_level: LogLevel = DEFAULT_LOG_LEVEL,
        log_format: str = DEFAULT_LOG_FORMAT,
        date_format: str = DEFAULT_DATE_FORMAT,
    ) -> Self:
        """Sets up the default logging configuration.

        Read more about log_levels, log_format, and date_format in `Python documentation (logging) <https://docs.python.org/3/library/logging.html>`.

        :param log_level: The logging level to set.
        :param log_format: The format of the log messages.
        :param date_format: The format for timestamps in log messages.
        :return: The instance of the SDK with logging configured.
        """
        setup_default_logging(
            log_level=log_level,
            log_format=log_format,
            date_format=date_format,
        )
        return self

    def _init_domains(self) -> None:
        """Initializes domain members by creating instances of them.

        This method inspects the class for any members that are subclasses of
        BaseDomain and initializes them.
        """
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member in members.items():
            if inspect.isclass(member) and issubclass(member, BaseDomain):
                resource = member(name=member_name, sdk=self)
                setattr(self, member_name, resource)

    def _get_endpoint(self, endpoint: UndefinedOr[str]) -> str:
        """Retrieves the API endpoint.

        If the endpoint is defined, it will be returned. Otherwise, it checks for
        an environment variable and defaults to a predefined endpoint.

        :param endpoint: An optional, customized endpoint.
        :return: The resolved API endpoint as a string.
        """
        if is_defined(endpoint):
            return endpoint

        if env_endpoint := os.getenv('YC_API_ENDPOINT'):
            return env_endpoint

        return 'api.cloud.yandex.net:443'

    # NB: All typehints on these classes must be 3.8-compatible
    # to properly work with get_annotations
    _event_loop: asyncio.AbstractEventLoop | None = None
    _loop_thread: threading.Thread | None = None
    _number: int = 0
    _lock = threading.Lock()

    @classmethod
    def _start_event_loop(cls):
        """Starts the event loop in a separate thread.

        This method sets the event loop for the current thread and runs it
        infinitely.
        """
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


@doc_from(BaseSDK)
class AsyncYCloudML(BaseSDK):
    tools: AsyncTools
    models: AsyncModels
    files: AsyncFiles
    threads: AsyncThreads
    assistants: AsyncAssistants
    runs: AsyncRuns
    search_api: AsyncSearchAPIDomain
    search_indexes: AsyncSearchIndexes
    datasets: AsyncDatasets
    tuning: AsyncTuning
    _messages: AsyncMessages


@doc_from(BaseSDK)
class YCloudML(BaseSDK):
    tools: Tools
    models: Models
    files: Files
    threads: Threads
    assistants: Assistants
    runs: Runs
    search_api: SearchAPIDomain
    search_indexes: SearchIndexes
    datasets: Datasets
    tuning: Tuning
    _messages: Messages
