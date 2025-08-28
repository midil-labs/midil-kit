from midil.event.consumer.strategies.base import EventConsumer
from midil.event.exceptions import (
    ConsumerStartError,
    ConsumerStopError,
)
from loguru import logger
import asyncio
from typing import Any
from pydantic import Field
from midil.event.consumer.strategies.base import EventConsumerConfig
from abc import abstractmethod


class PullEventConsumerConfig(EventConsumerConfig):
    interval: float = Field(
        default=1.0, description="Interval between polls if no messages"
    )


class PullEventConsumer(EventConsumer):
    def __init__(self, config: PullEventConsumerConfig):
        self._config: PullEventConsumerConfig = config
        self._running: bool = False
        self._loop_task: asyncio.Task[Any] | None = None

    @abstractmethod
    async def _poll_loop(self) -> None:
        ...

    async def start(self) -> None:
        try:
            logger.info(f"Starting consumer {self.__class__.__name__}")
            self._running = True
            self._loop_task = asyncio.create_task(self._poll_loop())
        except Exception as e:
            logger.error(f"An error occured while attempting to start consumer: {e}")
            raise ConsumerStartError(
                f"An error occured while attempting to start consumer: {e}"
            )

    async def stop(self) -> None:
        try:
            await self._close()
        except Exception as e:
            logger.error(f"An error occured while attempting to close consumer: {e}")
            raise ConsumerStopError(
                f"An error occured while attempting to close consumer: {e}"
            )
        finally:
            await self._reset_state()

    async def _reset_state(self) -> None:
        self._running = False
        self._subscribers.clear()
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass  # Expected when task is cancelled
            self._loop_task = None

    async def _close(self) -> None:
        """
        Close the consumer and release any resources.
        Override this method in subclasses if cleanup is needed.
        """
        pass
