from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from .backoff import BackoffStrategy, ExponentialBackoffWithJitter
from .dispatcher import EventDispatcher, HandlerSpec
from .queues import EventQueue
from .retry import RetryPolicy, SimpleRetryPolicy
from .types import Event

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Processes a single message using the registered handlers."""

    def __init__(
        self,
        dispatcher: EventDispatcher,
        queue: EventQueue,
        retry_policy: RetryPolicy,
        backoff: BackoffStrategy,
        visibility_on_retry: int = 10,
    ) -> None:
        self.dispatcher = dispatcher
        self.queue = queue
        self.retry_policy = retry_policy
        self.backoff = backoff
        self.visibility_on_retry = visibility_on_retry

    async def process(self, body: Event, receipt_handle: str) -> bool:
        """Return True if processed successfully (delete), False otherwise."""
        event_type = body.get("type")
        if not event_type:
            logger.warning("Message missing 'type' field; discarding.")
            return True

        specs = self.dispatcher.handlers_for(event_type)
        if not specs:
            logger.info("No handlers for %s, treating as success.", event_type)
            return True

        tasks = [
            self._process_handler_with_retries(spec, body, receipt_handle)
            for spec in specs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_ok = True
        for r in results:
            if isinstance(r, Exception):
                logger.exception("Handler failed with exception: %s", r)
                all_ok = False
            elif r is False:
                all_ok = False

        return all_ok

    async def _process_handler_with_retries(
        self, spec: HandlerSpec, event: Event, receipt_handle: str
    ) -> bool:
        attempt = 0
        while True:
            attempt += 1
            last_exc: Exception = Exception("handler error")
            try:
                await self.dispatcher.dispatch_single(spec, event)
                return True
            except asyncio.TimeoutError:
                logger.warning(
                    "Handler timed out. event=%s handler=%s attempt=%d",
                    event.get("type"),
                    spec.handler,
                    attempt,
                )
                last_exc = asyncio.TimeoutError()
            except Exception as exc:  # noqa: BLE001 - allow broad to drive retry
                logger.exception(
                    "Handler raised exception. event=%s handler=%s attempt=%d",
                    event.get("type"),
                    spec.handler,
                    attempt,
                )
                last_exc = exc

            if not self.retry_policy.should_retry(attempt, last_exc):
                logger.info(
                    "No more retries for handler=%s (attempt=%d).",
                    spec.handler,
                    attempt,
                )
                return False

            try:
                await self.queue.change_message_visibility(
                    receipt_handle, self.visibility_on_retry
                )
            except Exception:
                logger.exception(
                    "Failed to change message visibility on retry; continuing."
                )

            delay = self.backoff.next_delay(attempt)
            logger.info(
                "Retrying handler=%s attempt=%d after %.2fs",
                spec.handler,
                attempt,
                delay,
            )
            await asyncio.sleep(delay)


class PollingEventProcessor:
    """
    Poll a queue in a loop, dispatch messages to MessageProcessor, handle batch deletes and concurrency.
    """

    def __init__(
        self,
        queue: EventQueue,
        dispatcher: EventDispatcher,
        retry_policy: Optional[RetryPolicy] = None,
        backoff_strategy: Optional[BackoffStrategy] = None,
        *,
        max_messages: int = 10,
        wait_time: int = 20,
        poll_interval: float = 1.0,
        visibility_timeout: int = 60,
        concurrency: int = 10,
    ) -> None:
        self.queue = queue
        self.dispatcher = dispatcher
        self.retry_policy = retry_policy or SimpleRetryPolicy()
        self.backoff_strategy = backoff_strategy or ExponentialBackoffWithJitter()
        self.max_messages = max_messages
        self.wait_time = wait_time
        self.poll_interval = poll_interval
        self.visibility_timeout = visibility_timeout
        self._concurrency = concurrency
        self._running = False
        self._semaphore = asyncio.Semaphore(concurrency)
        self._task: Optional[asyncio.Task[None]] = None

    async def _handle_single_message(self, msg: Dict[str, Any]) -> Optional[str]:
        receipt = msg.get("ReceiptHandle")
        if not isinstance(receipt, str):
            return None
        logger.info(f"Processing message. receipt={receipt}")
        body_text = msg.get("Body", "")
        try:
            body: Event = json.loads(body_text)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON message; deleting. body=%s", body_text)
            return receipt

        async with self._semaphore:
            processor = MessageProcessor(
                dispatcher=self.dispatcher,
                queue=self.queue,
                retry_policy=self.retry_policy,
                backoff=self.backoff_strategy,
                visibility_on_retry=min(self.visibility_timeout, 30),
            )

            success = await processor.process(body, receipt)
            return receipt if success else None

    async def _poll_loop(self) -> None:
        logger.info("Starting poll loop")
        while self._running:
            try:
                messages = await self.queue.receive_messages(
                    max_messages=self.max_messages,
                    wait_time=self.wait_time,
                    visibility_timeout=self.visibility_timeout,
                )

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

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await self._task
        try:
            await self.queue.close()
        except Exception:
            logger.exception("Error closing queue.")


__all__ = [
    "MessageProcessor",
    "PollingEventProcessor",
]
