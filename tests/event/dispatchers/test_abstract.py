import pytest
import anyio
from unittest.mock import AsyncMock, patch
from typing import Any

from midil.event.dispatchers.abstract import AbstractEventDispatcher
from midil.event.context import EventContext

pytestmark = pytest.mark.anyio


class ConcreteEventDispatcher(AbstractEventDispatcher):
    """Concrete implementation for testing."""

    def __init__(self):
        super().__init__()
        self._notify_mock = AsyncMock()

    async def _notify(self, event: str, body: dict[str, Any]) -> None:
        return await self._notify_mock(event, body)


class TestAbstractEventDispatcher:
    """Tests for AbstractEventDispatcher abstract base class."""

    def test_is_abstract(self):
        """Test that AbstractEventDispatcher cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            AbstractEventDispatcher()  # type: ignore

    def test_concrete_implementation(self):
        """Test that concrete implementation can be instantiated."""
        dispatcher = ConcreteEventDispatcher()
        assert isinstance(dispatcher, AbstractEventDispatcher)
        assert hasattr(dispatcher, "event_queue")
        assert hasattr(dispatcher, "receive_stream")

    def test_init_creates_queue(self):
        """Test that initialization creates an event queue."""
        dispatcher = ConcreteEventDispatcher()
        assert hasattr(dispatcher, "event_queue")
        assert hasattr(dispatcher, "receive_stream")
        # Check that the streams are properly configured
        assert dispatcher.event_queue is not None
        assert dispatcher.receive_stream is not None

    async def test_start_event_processor(self):
        """Test that start_event_processor starts the worker."""
        dispatcher = ConcreteEventDispatcher()

        with patch.object(dispatcher, "_event_worker") as mock_worker:
            # Since start_event_processor uses a task group and runs the worker,
            # we need to mock the worker to prevent it from running indefinitely
            mock_worker.return_value = None

            # Use a timeout to prevent hanging if something goes wrong
            with anyio.fail_after(1.0):
                await dispatcher.start_event_processor()

            mock_worker.assert_called_once()

    @patch("midil.event.dispatchers.abstract.get_current_event")
    async def test_notify_queues_event(self, mock_get_current_event):
        """Test that notify method queues events correctly."""
        dispatcher = ConcreteEventDispatcher()

        # Mock current event context
        mock_context = EventContext(id="test-id", event_type="test.event")
        mock_get_current_event.return_value = mock_context

        event_name = "user.created"
        event_body = {"user_id": "123", "email": "test@example.com"}

        await dispatcher.notify(event_name, event_body)

        # Get the queued item from the receive stream
        (
            queued_context,
            queued_event,
            queued_body,
        ) = await dispatcher.receive_stream.receive()

        assert queued_event == event_name
        assert queued_body == event_body
        # Should be a deep copy of the context
        assert queued_context.id == mock_context.id
        assert queued_context.event_type == mock_context.event_type
        assert queued_context is not mock_context  # Should be a copy

    @patch("midil.event.dispatchers.abstract.get_current_event")
    async def test_notify_multiple_events(self, mock_get_current_event):
        """Test queuing multiple events."""
        dispatcher = ConcreteEventDispatcher()

        mock_context = EventContext(id="test-id", event_type="test.event")
        mock_get_current_event.return_value = mock_context

        events = [
            ("event1", {"data": "1"}),
            ("event2", {"data": "2"}),
            ("event3", {"data": "3"}),
        ]

        # Queue all events
        for event_name, event_body in events:
            await dispatcher.notify(event_name, event_body)

        # Verify all events are queued correctly
        for expected_event, expected_body in events:
            context, event, body = await dispatcher.receive_stream.receive()
            assert event == expected_event
            assert body == expected_body

    async def test_event_worker_processes_events(self):
        """Test that event worker processes queued events."""
        dispatcher = ConcreteEventDispatcher()

        # Create a test event context
        test_context = EventContext(id="worker-test", event_type="worker.test")
        test_event = "test.event"
        test_body = {"test": "data"}

        # Manually add an event to the queue
        await dispatcher.event_queue.send((test_context, test_event, test_body))

        # Start the worker in a task group with a timeout
        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                # Give it time to process one event
                await anyio.sleep(0.1)
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # Verify the event was processed
        dispatcher._notify_mock.assert_called_once_with(test_event, test_body)

    async def test_event_worker_handles_exceptions(self):
        """Test that event worker handles exceptions gracefully."""
        dispatcher = ConcreteEventDispatcher()

        # Make _notify raise an exception
        dispatcher._notify_mock.side_effect = Exception("Processing error")

        test_context = EventContext(id="error-test", event_type="error.test")
        await dispatcher.event_queue.send(
            (test_context, "error.event", {"error": True})
        )

        # Mock logger to capture exception logging
        with patch("midil.event.dispatchers.abstract.logger") as mock_logger:

            async def run_worker_briefly():
                async with anyio.create_task_group() as tg:
                    tg.start_soon(dispatcher._event_worker)
                    # Give it time to process and handle the exception
                    await anyio.sleep(0.1)
                    tg.cancel_scope.cancel()

            try:
                await run_worker_briefly()
            except anyio.get_cancelled_exc_class():
                pass

            # Verify exception was logged
            mock_logger.exception.assert_called()

    async def test_event_worker_marks_tasks_done(self):
        """Test that event worker marks queue tasks as done."""
        dispatcher = ConcreteEventDispatcher()

        test_context = EventContext(id="done-test", event_type="done.test")
        await dispatcher.event_queue.send((test_context, "done.event", {}))

        # With anyio memory streams, we don't need to track task_done manually
        # The stream handles this automatically, so we just verify the event is processed
        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                await anyio.sleep(0.1)
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # Verify the event was processed (which means the stream was consumed)
        dispatcher._notify_mock.assert_called_once_with("done.event", {})

    @patch("midil.event.dispatchers.abstract.event_context")
    async def test_event_worker_uses_event_context(self, mock_event_context):
        """Test that event worker uses event context manager."""
        dispatcher = ConcreteEventDispatcher()

        test_context = EventContext(id="context-test", event_type="context.test")

        # Setup async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = test_context
        mock_context_manager.__aexit__.return_value = None
        mock_event_context.return_value = mock_context_manager

        await dispatcher.event_queue.send((test_context, "context.event", {}))

        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                await anyio.sleep(0.1)
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # Verify event_context was called with correct parameters
        mock_event_context.assert_called_once_with(
            test_context.event_type, parent_override=test_context
        )

    @patch("midil.event.dispatchers.abstract.logger")
    async def test_event_worker_logging(self, mock_logger):
        """Test that event worker logs appropriately."""
        dispatcher = ConcreteEventDispatcher()

        # Start worker briefly to trigger startup log
        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                await anyio.sleep(0.01)  # Give it time to start
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # Verify startup log
        mock_logger.info.assert_called_with(
            f"Started {dispatcher.__class__.__name__} event worker loop"
        )

    @patch("midil.event.dispatchers.abstract.logger")
    async def test_event_worker_contextualized_logging(self, mock_logger):
        """Test that event worker uses contextualized logging."""
        dispatcher = ConcreteEventDispatcher()

        test_context = EventContext(id="log-test", event_type="log.test")
        await dispatcher.event_queue.send((test_context, "log.event", {}))

        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                await anyio.sleep(0.1)
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # Verify contextualize was called with correct parameters
        mock_logger.contextualize.assert_called_with(
            event_id=test_context.id, event_type=test_context.event_type
        )

    async def test_event_worker_infinite_loop(self):
        """Test that event worker runs in an infinite loop."""
        dispatcher = ConcreteEventDispatcher()

        # Add multiple events
        for i in range(3):
            context = EventContext(id=f"loop-{i}", event_type=f"loop.{i}")
            await dispatcher.event_queue.send((context, f"event.{i}", {"index": i}))

        async def run_worker_briefly():
            async with anyio.create_task_group() as tg:
                tg.start_soon(dispatcher._event_worker)
                await anyio.sleep(0.2)  # Give time to process multiple events
                tg.cancel_scope.cancel()

        try:
            await run_worker_briefly()
        except anyio.get_cancelled_exc_class():
            pass

        # All three events should have been processed
        assert dispatcher._notify_mock.call_count == 3

    def test_abstract_notify_method(self):
        """Test that _notify is abstract and must be implemented."""
        # This is already tested by testing ConcreteEventDispatcher,
        # but let's verify the abstract nature
        from abc import ABC

        assert issubclass(AbstractEventDispatcher, ABC)

        # Check that _notify is in __abstractmethods__
        abstract_methods: set[str] = getattr(
            AbstractEventDispatcher, "__abstractmethods__", set()
        )
        assert "_notify" in abstract_methods

    async def test_queue_type_safety(self):
        """Test that the queue is properly typed."""
        dispatcher = ConcreteEventDispatcher()

        # The queue should be typed for the correct tuple type
        assert hasattr(dispatcher, "event_queue")

        # We can't easily test the generic type at runtime,
        # but we can test that it accepts the expected data
        context = EventContext(id="type-test", event_type="type.test")
        await dispatcher.event_queue.send((context, "event", {"data": "test"}))

        item = await dispatcher.receive_stream.receive()
        assert isinstance(item, tuple)
        assert len(item) == 3
        assert isinstance(item[0], EventContext)
        assert isinstance(item[1], str)
        assert isinstance(item[2], dict)

    @patch("midil.event.dispatchers.abstract.deepcopy")
    @patch("midil.event.dispatchers.abstract.get_current_event")
    async def test_notify_uses_deepcopy(self, mock_get_current_event, mock_deepcopy):
        """Test that notify uses deepcopy for the event context."""
        dispatcher = ConcreteEventDispatcher()

        original_context = EventContext(id="original", event_type="original.event")
        copied_context = EventContext(id="copied", event_type="copied.event")

        mock_get_current_event.return_value = original_context
        mock_deepcopy.return_value = copied_context

        await dispatcher.notify("test.event", {"data": "test"})

        # deepcopy should have been called with the original context
        mock_deepcopy.assert_called_once_with(original_context)

        # The copied context should be in the stream
        queued_context, _, _ = await dispatcher.receive_stream.receive()
        assert queued_context == copied_context
