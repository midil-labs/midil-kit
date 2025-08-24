from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Set
from typing import get_origin
import inspect

from midil.event.consumer.core.types import (
    FailurePolicy,
    HandlerContext,
    HandlerName,
    HandlerStatus,
    HandlerState,
    MessageState,
    Event,
    HandlerCallable,
)
from midil.event.consumer.core.router import HandlerSpec, EventRouter
from midil.event.consumer.core.state_store import StateStore
from midil.event.consumer.core.types import Depends
from loguru import logger


class EventDispatcher:
    """Execute handler dependency graphs with concurrency and retries."""

    def __init__(
        self,
        router: EventRouter,
        state_store: StateStore,
        concurrency_limit: int = 10,
        default_failure_policy: FailurePolicy = FailurePolicy.ABORT,
    ) -> None:
        self.router = router
        self.state_store = state_store
        self.concurrency_limit = concurrency_limit
        self.default_failure_policy = default_failure_policy

    async def dispatch(
        self,
        message_id: str,
        event: Event,
        receipt_handle: str,
        queue: Optional[object] = None,
    ) -> bool:
        event_type = event.get("type", "unknown")
        handlers = self.router.handlers_for(event_type)
        if not handlers:
            logger.warning(f"No handlers registered for event type '{event_type}'")
            return True
        logger.debug(
            f"Executing handlers {list(handlers.keys())} for event type '{event_type}'"
        )
        message_state = MessageState(message_id=message_id)
        for name in handlers.keys():
            message_state.handler_states[name] = HandlerState()
        await self.state_store.init_message(message_id, list(handlers.keys()))

        try:
            success = await self._execute_handler_graph(
                handlers, message_state, event, receipt_handle, queue
            )
            message_state.overall_status = "completed" if success else "failed"
            return success
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during dispatch of event '{event_type}': {type(e).__name__}: {e}",
                exc_info=True,
            )
            message_state.overall_status = "error"
            return False

    async def _execute_handler_graph(
        self,
        handlers: Dict[HandlerName, HandlerSpec],
        message_state: MessageState,
        event: Event,
        receipt_handle: str,
        queue: Optional[object],
    ) -> bool:
        dependents_map = self._build_dependents_map(handlers)
        ready_queue: deque[HandlerName] = deque(
            [name for name, spec in handlers.items() if not spec.depends_on]
        )
        in_progress: Set[HandlerName] = set()
        completed: Set[HandlerName] = set()
        failed: Set[HandlerName] = set()

        semaphore = asyncio.Semaphore(self.concurrency_limit)
        running_tasks: Set[asyncio.Task[None]] = set()

        logger.debug(
            f"Starting handler graph execution. Initial ready_queue: {list(ready_queue)}"
        )

        while ready_queue or running_tasks:
            while ready_queue and len(running_tasks) < self.concurrency_limit:
                handler_name = ready_queue.popleft()
                if handler_name not in in_progress:
                    logger.debug(
                        f"Scheduling handler '{handler_name}' for execution. "
                        f"In progress: {in_progress}, Completed: {completed}, Failed: {failed}"
                    )
                    in_progress.add(handler_name)
                    task = asyncio.create_task(
                        self._run_and_handle_completion(
                            handler_name,
                            handlers[handler_name],
                            message_state,
                            event,
                            receipt_handle,
                            queue,
                            semaphore,
                            dependents_map,
                            ready_queue,
                            in_progress,
                            completed,
                            failed,
                        )
                    )
                    running_tasks.add(task)
                else:
                    logger.debug(
                        f"Handler '{handler_name}' is already in progress, skipping scheduling."
                    )

            if running_tasks:
                logger.debug(
                    f"Waiting for {len(running_tasks)} running task(s) to complete. "
                    f"Current ready_queue: {list(ready_queue)}"
                )
                done, running_tasks = await asyncio.wait(
                    running_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    await task

        response = self._evaluate_final_success(handlers, completed, failed)
        logger.debug(
            f"Handler graph execution finished. Completed: {completed}, Failed: {failed}"
        )
        return response

    async def _run_and_handle_completion(
        self,
        handler_name: HandlerName,
        spec: HandlerSpec,
        message_state: MessageState,
        event: Event,
        receipt_handle: str,
        queue: Optional[object],
        semaphore: asyncio.Semaphore,
        dependents_map: Dict[HandlerName, Set[HandlerName]],
        ready_queue: "deque[HandlerName]",
        in_progress: Set[HandlerName],
        completed: Set[HandlerName],
        failed: Set[HandlerName],
    ) -> None:
        async with semaphore:
            try:
                result = await self._run_handler_with_retries(
                    spec, message_state, event, receipt_handle, queue
                )
                message_state.handler_states[
                    handler_name
                ].status = HandlerStatus.SUCCEEDED
                message_state.handler_states[handler_name].result = result
                message_state.results[handler_name] = result

                await self.state_store.save_handler_result(
                    message_state.message_id,
                    handler_name,
                    result,
                    message_state.handler_states[handler_name].attempts,
                    "succeeded",
                )

                completed.add(handler_name)
                in_progress.discard(handler_name)

                self._schedule_ready_dependents(
                    handler_name,
                    dependents_map,
                    spec.failure_policy,
                    completed,
                    failed,
                    ready_queue,
                    in_progress,
                    message_state,
                )
            except Exception as e:
                logger.error(
                    f"Handler '{handler_name}' encountered an error ({type(e).__name__}): {e}",
                    exc_info=True,
                )
                message_state.handler_states[handler_name].status = HandlerStatus.FAILED
                message_state.handler_states[handler_name].last_error = e
                await self.state_store.mark_handler_failed(
                    message_state.message_id, handler_name, e
                )
                failed.add(handler_name)
                in_progress.discard(handler_name)

                if spec.failure_policy == FailurePolicy.ABORT:
                    logger.info(
                        f"Aborting dependent handlers due to failure of '{handler_name}'"
                    )
                    self._mark_dependents_skipped(
                        handler_name, dependents_map, message_state
                    )
                else:
                    logger.info(
                        f"Continuing with dependent handlers despite failure of '{handler_name}'"
                    )
                    self._schedule_ready_dependents(
                        handler_name,
                        dependents_map,
                        spec.failure_policy,
                        completed,
                        failed,
                        ready_queue,
                        in_progress,
                        message_state,
                    )

    async def _run_handler_with_retries(
        self,
        spec: HandlerSpec,
        message_state: MessageState,
        event: Event,
        receipt_handle: str,
        queue: Optional[Any],
    ) -> Any:
        """Execute a handler with retry logic and dependency injection"""

        handler_state = message_state.handler_states[spec.name]
        last_exception = None

        for attempt in range(1, spec.retry_policy.max_attempts() + 1):
            handler_state.attempts = attempt
            handler_state.status = HandlerStatus.RUNNING

            try:
                context = HandlerContext(
                    event=event,
                    deps_results=message_state.results.copy(),
                    attempt=attempt,
                    message_id=message_state.message_id,
                    metadata=spec.metadata,
                )

                dep_kwargs = await self._resolve_dependencies(spec.handler, context)
                async with asyncio.timeout(spec.timeout_seconds):
                    result = await spec.handler(context, **dep_kwargs)
                return result

            except Exception as e:
                last_exception = e
                logger.error(
                    f"Handler '{spec.name}' attempt {attempt} failed: {type(e).__name__}: {e}",
                    exc_info=True,  # Include full stack trace
                )

                if spec.retry_policy.should_retry(attempt, e):
                    if queue:
                        try:
                            await queue.change_message_visibility(
                                receipt_handle, visibility_seconds=30
                            )
                        except Exception as visibility_error:
                            logger.error(
                                f"Failed to update message visibility for handler '{spec.name}': {visibility_error}",
                                exc_info=True,
                            )
                    delay = spec.backoff.next_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Handler '{spec.name}' will not retry - error is not retryable"
                    )
                    break

        raise last_exception or Exception("Handler failed without specific error")

    async def _resolve_dependencies(
        self, func: HandlerCallable, ctx: HandlerContext
    ) -> dict[str, Any]:
        sig = inspect.signature(func)
        kwargs = {}

        for name, param in sig.parameters.items():
            ann = param.annotation
            # Handle case where it's `HandlerContext` directly or wrapped in typing.Annotated
            if ann is HandlerContext or get_origin(ann) is HandlerContext:
                continue  # skip, we inject it positionally

            default = param.default
            if isinstance(default, Depends):
                dep_func = default.dependency
                if inspect.iscoroutinefunction(dep_func):
                    kwargs[name] = await dep_func()
                else:
                    kwargs[name] = dep_func()
        return kwargs

    def _build_dependents_map(
        self, handlers: Dict[HandlerName, HandlerSpec]
    ) -> Dict[HandlerName, Set[HandlerName]]:
        dependents_map: Dict[HandlerName, Set[HandlerName]] = defaultdict(set)
        for name, spec in handlers.items():
            for dep in spec.depends_on:
                dependents_map[dep].add(name)
        return dependents_map

    def _schedule_ready_dependents(
        self,
        completed_handler: HandlerName,
        dependents_map: Dict[HandlerName, Set[HandlerName]],
        failure_policy: FailurePolicy,
        completed: Set[HandlerName],
        failed: Set[HandlerName],
        ready_queue: "deque[HandlerName]",
        in_progress: Set[HandlerName],
        message_state: MessageState,
    ) -> None:
        for dependent in dependents_map.get(completed_handler, set()):
            if (
                dependent not in completed
                and dependent not in failed
                and dependent not in in_progress
                and dependent not in ready_queue
            ):
                dep_spec = None
                # Look up the dependent spec across all event types
                for handlers in self.router._handlers.values():
                    if dependent in handlers:
                        dep_spec = handlers[dependent]
                        break
                if dep_spec and self._all_dependencies_satisfied(
                    dep_spec, completed, failed, failure_policy
                ):
                    ready_queue.append(dependent)

    def _all_dependencies_satisfied(
        self,
        spec: HandlerSpec,
        completed: Set[HandlerName],
        failed: Set[HandlerName],
        failure_policy: FailurePolicy,
    ) -> bool:
        for dep in spec.depends_on:
            if dep in failed and failure_policy == FailurePolicy.ABORT:
                return False
            if dep not in completed and dep not in failed:
                return False
        return True

    def _mark_dependents_skipped(
        self,
        failed_handler: HandlerName,
        dependents_map: Dict[HandlerName, Set[HandlerName]],
        message_state: MessageState,
    ) -> None:
        to_skip = list(dependents_map.get(failed_handler, set()))
        while to_skip:
            dependent = to_skip.pop(0)
            if message_state.handler_states[dependent].status == HandlerStatus.PENDING:
                message_state.handler_states[dependent].status = HandlerStatus.SKIPPED
                to_skip.extend(list(dependents_map.get(dependent, set())))

    def _evaluate_final_success(
        self,
        handlers: Dict[HandlerName, HandlerSpec],
        completed: Set[HandlerName],
        failed: Set[HandlerName],
    ) -> bool:
        for name, spec in handlers.items():
            if spec.failure_policy == FailurePolicy.ABORT and name in failed:
                return False
        return True
