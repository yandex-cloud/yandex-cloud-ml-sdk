from __future__ import annotations

from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun


def make_async_run_manager(manager:CallbackManagerForLLMRun) -> AsyncCallbackManagerForLLMRun:
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
