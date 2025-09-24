# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.schemas import JsonObject


class ToolCallsBuffer:
    """
    Buffer for accumulating tool calls from streaming responses.
    
    Manages multiple ToolCallBuffer instances, one for each tool call index,
    and provides access to the complete list of tool calls.
    """
    
    def __init__(self) -> None:
        self._buffer: dict[str, ToolCallBuffer] = {}

    def update(self, tool_calls_delta: JsonObject) -> None:
        """Update the buffer with new tool call delta data.
        
        :param tool_calls_delta: List of tool call delta objects from stream
        """
        assert isinstance(tool_calls_delta, list)
        for tool_call_delta in tool_calls_delta:
            assert isinstance(tool_call_delta, dict)
            assert 'index' in tool_call_delta
            index = tool_call_delta['index']
            assert isinstance(index, int)
            buffer = self._buffer.setdefault(index, ToolCallBuffer())
            buffer.update(tool_call_delta)

    @property
    def value(self) -> list[JsonObject]:
        """Get the complete list of tool calls."""
        items = sorted(self._buffer.items())
        return [buffer.value for _, buffer in items]


class ToolCallBuffer:
    """
    Buffer for accumulating a single tool call from streaming responses.
    
    Handles incremental updates to tool call data, building up the complete
    tool call object as delta information arrives from the stream.
    """
    
    def __init__(self) -> None:
        self._buffer: dict[str, str] = {}
        self._function_buffer: dict[str, str] = {}
        self._index: int | None = None

    def update(self, tool_call_delta: JsonObject) -> None:
        """Update the buffer with new tool call delta data.
        
        :param tool_call_delta: Tool call delta object from stream
        """
        if type_ := tool_call_delta.get('type'):
            if type_ != 'function':
                raise RuntimeError(
                    'Do not know what to do with non-function tool call; try to upgrade SDK'
                )

        index = tool_call_delta.get('index')
        if index is not None:
            assert isinstance(index, int)
            self._index = index

        for field in ('id', 'type'):
            if value := tool_call_delta.get(field):
                assert isinstance(value, str)
                self._buffer[field] = value

        function = tool_call_delta.get('function')
        if not function:
            return

        assert isinstance(function, dict)

        for field in ('name', 'arguments'):
            self._function_buffer.setdefault(field, '')
            value = function.get(field, '')
            assert isinstance(value, str)
            self._function_buffer[field] += value

    @property
    def value(self) -> JsonObject:
        """Get the complete tool call object."""
        if self._index is None:
            raise RuntimeError('missing stream record with index value')

        return {
            'function': self._function_buffer,  # type: ignore[dict-item]
            'index': self._index,
            **self._buffer,
        }
