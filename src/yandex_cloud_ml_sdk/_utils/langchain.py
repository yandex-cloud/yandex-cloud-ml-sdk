from __future__ import annotations

from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun


def make_async_run_manager(manager:CallbackManagerForLLMRun) -> AsyncCallbackManagerForLLMRun:
    """
    Convert a synchronous callback manager to an asynchronous callback manager.

    This utility function creates an AsyncCallbackManagerForLLMRun instance from
    a CallbackManagerForLLMRun by transferring all the relevant properties like
    handlers, metadata, tags, and run identifiers.

    :param manager: The synchronous callback manager to convert.

    .. note::
       This function is useful when you need to bridge synchronous and asynchronous
       callback handling in LangChain integrations.
    """
    return AsyncCallbackManagerForLLMRun(
        run_id=manager.run_id,
        handlers=manager.handlers,
        inheritable_handlers=manager.inheritable_handlers,
        parent_run_id=manager.parent_run_id,
        tags=manager.tags,
        inheritable_tags=manager.inheritable_tags,
        metadata=manager.metadata,
        inheritable_metadata=manager.inheritable_metadata,
    )
