import anyio
from abc import ABC, abstractmethod
from copy import deepcopy
from loguru import logger
from typing import Any, ClassVar, Dict
from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream

from midil.event.context import (
    get_current_event,
    event_context,
    EventContext,
)


class AbstractEventDispatcher(ABC):
    _MAX_BUFFER_SIZE: ClassVar[int] = 1000

    def __init__(self) -> None:
        send_stream: MemoryObjectSendStream[tuple[EventContext, str, Dict[str, Any]]]
        receive_stream: MemoryObjectReceiveStream[
            tuple[EventContext, str, Dict[str, Any]]
        ]
        send_stream, receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=self._MAX_BUFFER_SIZE
        )
        self.event_queue = send_stream
        self.receive_stream = receive_stream

    async def start_event_processor(self) -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._event_worker)

    async def _event_worker(self) -> None:
        logger.info(f"Started {self.__class__.__name__} event worker loop")
        async with self.receive_stream:
            async for event_ctx, event, body in self.receive_stream:
                with logger.contextualize(
                    event_id=event_ctx.id, event_type=event_ctx.event_type
                ):
                    try:
                        async with event_context(
                            event_ctx.event_type, parent_override=event_ctx
                        ) as event_ctx:
                            await self._notify(event, body)
                    except Exception as e:
                        logger.exception(f"Failed processing event {event}: {e}")

    async def notify(self, event: str, body: dict[str, Any]) -> None:
        logger.debug(f"Queueing event: {event} with body: {body}")
        await self.event_queue.send((deepcopy(get_current_event()), event, body))

    @abstractmethod
    async def _notify(self, event: str, body: dict[str, Any]) -> None:
        ...
