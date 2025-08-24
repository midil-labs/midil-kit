from typing import Optional, Dict, Any
import asyncio
import json
from loguru import logger
from midil.event.consumer.core.dispatcher import EventDispatcher
from midil.event.consumer.core.state_store import StateStore, InMemoryStateStore
from midil.event.consumer.core.types import Event
from midil.event.consumer.queues.base import EventQueue
from midil.event.consumer.core.router import EventRouter
from midil.event.consumer.strategies.base import BaseEventStrategy


class PollingEventStrategy(BaseEventStrategy):
    """
    Poll a queue in a loop, dispatch messages to MessageProcessor,
    handle batch deletes and concurrency, with clean shutdown support.
    """

    def __init__(
        self,
        queue: EventQueue,
        router: EventRouter,
        state_store: Optional[StateStore] = None,
        *,
        max_messages: int = 10,
        wait_time: int = 20,
        poll_interval: float = 1.0,
        visibility_timeout: int = 60,
        concurrency: int = 10,
    ) -> None:
        self.queue = queue
        self.registry = router
        self.max_messages = max_messages
        self.wait_time = wait_time
        self.poll_interval = poll_interval
        self.visibility_timeout = visibility_timeout
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._task: Optional[asyncio.Task[None]] = None
        self._shutdown = asyncio.Event()
        self.state_store: StateStore = state_store or InMemoryStateStore()

    async def _handle_single_message(self, msg: Dict[str, Any]) -> Optional[str]:
        receipt = msg.get("ReceiptHandle")
        if not isinstance(receipt, str):
            return None

        logger.debug(f"Processing message. receipt={receipt}")
        body_text = msg.get("Body", "")
        try:
            body: Event = json.loads(body_text)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON message; deleting. body=%s", body_text)
            return receipt

        async with self._semaphore:
            dispatcher = EventDispatcher(
                router=self.registry,
                state_store=self.state_store,
                concurrency_limit=self._concurrency,
            )

            message_id = msg.get("MessageId", "")
            success = await dispatcher.dispatch(
                message_id=message_id,
                event=body,
                receipt_handle=receipt,
                queue=self.queue,
            )
            return receipt if success else None

    async def _poll_loop(self) -> None:
        logger.info("Starting poll loop")
        while not self._shutdown.is_set():
            try:
                # Race between receiving messages and shutdown
                logger.debug("Polling for messages")
                receive_task = asyncio.create_task(
                    self.queue.receive_messages(
                        max_messages=self.max_messages,
                        wait_time=self.wait_time,
                        visibility_timeout=self.visibility_timeout,
                    )
                )
                shutdown_task = asyncio.create_task(self._shutdown.wait())

                done, pending = await asyncio.wait(
                    {receive_task, shutdown_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Cancel whichever task didn't finish
                for task in pending:
                    task.cancel()

                # If shutdown was triggered, exit immediately
                if shutdown_task in done and self._shutdown.is_set():
                    break

                # Otherwise, process messages
                messages = await receive_task
                if not messages:
                    await asyncio.sleep(self.poll_interval)
                    continue

                tasks = [
                    asyncio.create_task(self._handle_single_message(m))
                    for m in messages
                ]
                results = await asyncio.gather(*tasks)

                receipts_to_delete = [r for r in results if r is not None]
                if receipts_to_delete:
                    try:
                        await self.queue.delete_messages_batch(receipts_to_delete)
                    except Exception:
                        logger.exception(
                            "Batch delete failed; will rely on queue redrive policy."
                        )

            except Exception:
                logger.exception("Poll loop encountered an error; backing off.")
                await asyncio.sleep(5)

        logger.info("Poll loop stopped")

    def start(self) -> None:
        if not self._shutdown.is_set() and self._task is None:
            self._shutdown.clear()
            self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._shutdown.set()
        if self._task:
            await self._task
            self._task = None
        try:
            await self.queue.close()
        except Exception:
            logger.exception("Error closing queue.")
