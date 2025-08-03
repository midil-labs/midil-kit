"""
Tests for midil.infrastructure.messaging.dispatchers.polling
"""
import pytest
import anyio
import inspect
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch
from collections import defaultdict

from midil.infrastructure.messaging.dispatchers.polling import (
    PollingEventDispatcher,
    dispatcher,
    Observer,
    FunctionalObserver,
    MethodObserver,
)

pytestmark = pytest.mark.anyio


class TestPollingEventDispatcher:
    """Tests for PollingEventDispatcher class."""

    @pytest.fixture
    def polling_dispatcher(self):
        """Create a fresh PollingEventDispatcher instance for each test."""
        dispatcher = PollingEventDispatcher()
        yield dispatcher
        # Clear observers after each test to ensure test isolation
        dispatcher._observers.clear()

    def test_inheritance(self, polling_dispatcher):
        """Test that PollingEventDispatcher inherits from AbstractEventDispatcher."""
        from midil.infrastructure.messaging.dispatchers.abstract import (
            AbstractEventDispatcher,
        )

        assert isinstance(polling_dispatcher, AbstractEventDispatcher)

    def test_observers_initialization(self, polling_dispatcher):
        """Test that _observers is properly initialized."""
        assert hasattr(polling_dispatcher, "_observers")
        assert isinstance(polling_dispatcher._observers, dict)
        # Should be a defaultdict that creates lists
        assert isinstance(polling_dispatcher._observers, defaultdict)

    def test_on_decorator_registration(self, polling_dispatcher):
        """Test the @on decorator for registering event handlers."""

        @polling_dispatcher.on("test.event")
        async def test_handler(event: str, body: dict):
            pass

        # Handler should be registered
        assert "test.event" in polling_dispatcher._observers
        assert test_handler in polling_dispatcher._observers["test.event"]

    def test_on_decorator_returns_original_function(self, polling_dispatcher):
        """Test that @on decorator returns the original function unchanged."""

        async def original_handler(event: str, body: dict):
            return "test_result"

        decorated_handler = polling_dispatcher.on("test.event")(original_handler)

        # Should return the same function
        assert decorated_handler is original_handler
        assert decorated_handler.__name__ == "original_handler"

    def test_on_decorator_multiple_events(self, polling_dispatcher):
        """Test registering handlers for multiple events."""

        @polling_dispatcher.on("event1")
        async def handler1(event: str, body: Dict[str, Any]):
            pass

        @polling_dispatcher.on("event2")
        async def handler2(event: str, body: Dict[str, Any]):
            pass

        @polling_dispatcher.on("event1")  # Same event, different handler
        async def handler3(event: str, body: Dict[str, Any]):
            pass

        assert len(polling_dispatcher._observers["event1"]) == 2
        assert len(polling_dispatcher._observers["event2"]) == 1
        assert handler1 in polling_dispatcher._observers["event1"]
        assert handler3 in polling_dispatcher._observers["event1"]
        assert handler2 in polling_dispatcher._observers["event2"]

    def test_register_method(self, polling_dispatcher):
        """Test the register method for adding observers."""

        async def test_observer(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("manual.event", test_observer)

        assert "manual.event" in polling_dispatcher._observers
        assert test_observer in polling_dispatcher._observers["manual.event"]

    def test_register_method_multiple_observers(self, polling_dispatcher):
        """Test registering multiple observers for the same event."""

        async def observer1(event: str, body: Dict[str, Any]):
            pass

        async def observer2(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("shared.event", observer1)
        polling_dispatcher.register("shared.event", observer2)

        assert len(polling_dispatcher._observers["shared.event"]) == 2
        assert observer1 in polling_dispatcher._observers["shared.event"]
        assert observer2 in polling_dispatcher._observers["shared.event"]

    async def test_notify_with_registered_observers(self, polling_dispatcher):
        """Test _notify method calls registered observers."""

        mock_observer1 = AsyncMock()
        mock_observer2 = AsyncMock()

        polling_dispatcher.register("test.notify", mock_observer1)
        polling_dispatcher.register("test.notify", mock_observer2)

        event_body = {"test": "data", "user_id": 123}

        with patch("anyio.create_task_group") as mock_create_task_group:
            # Mock the task group context manager
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("test.notify", event_body)

            # Should create task group and start tasks for both observers
            mock_create_task_group.assert_called()
            assert mock_tg.start_soon.call_count == 2

    async def test_notify_with_no_observers(self, polling_dispatcher):
        """Test _notify method with no registered observers."""

        with patch(
            "midil.infrastructure.messaging.dispatchers.polling.logger"
        ) as mock_logger:
            await polling_dispatcher._notify("nonexistent.event", {"data": "test"})

            # Should log warning about no handlers
            mock_logger.warning.assert_called_once()
            # Should log debug messages: processing event + available event types
            assert mock_logger.debug.call_count == 2

    async def test_notify_observer_task_creation(self, polling_dispatcher):
        """Test that observers are called via asyncio.create_task."""

        async def test_observer(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("task.test", test_observer)

        with patch("anyio.create_task_group") as mock_create_task_group:
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("task.test", {"test": "data"})

            mock_create_task_group.assert_called_once()
            # The task should be started with the observer function
            mock_tg.start_soon.assert_called_once()
            # Check the arguments passed to start_soon
            call_args = mock_tg.start_soon.call_args[0]
            assert (
                call_args[0] == test_observer
            )  # First arg should be the observer function
            assert call_args[1] == "task.test"  # Second arg should be the event
            assert call_args[2] == {"test": "data"}  # Third arg should be the body

    async def test_notify_method_observer_logging(self, polling_dispatcher):
        """Test logging for method observers vs function observers."""

        class TestClass:
            async def method_observer(self, event: str, body: Dict[str, Any]):
                pass

        test_instance = TestClass()

        async def function_observer(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("method.test", test_instance.method_observer)
        polling_dispatcher.register("function.test", function_observer)

        with patch(
            "midil.infrastructure.messaging.dispatchers.polling.logger"
        ) as mock_logger:
            with patch("anyio.create_task_group") as mock_create_task_group:
                mock_tg = Mock()
                mock_context_manager = Mock()
                mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
                mock_context_manager.__aexit__ = AsyncMock(return_value=None)
                mock_create_task_group.return_value = mock_context_manager

                await polling_dispatcher._notify("method.test", {})
                await polling_dispatcher._notify("function.test", {})

            # Should have different debug messages for methods vs functions
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]

            # Should contain class name for method observer
            assert any("TestClass" in msg for msg in debug_calls)
            # Should contain function name for function observer
            assert any("function_observer" in msg for msg in debug_calls)

    async def test_notify_only_coroutine_functions(self, polling_dispatcher):
        """Test that only coroutine functions are processed."""

        # Regular function (not async)
        def regular_function(event: str, body: Dict[str, Any]):
            pass

        # Async function
        async def async_function(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("mixed.test", regular_function)
        polling_dispatcher.register("mixed.test", async_function)

        with patch("anyio.create_task_group") as mock_create_task_group:
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("mixed.test", {})

            # Only the async function should result in a task creation
            assert mock_tg.start_soon.call_count == 1

    def test_observers_default_dict_behavior(self, polling_dispatcher):
        """Test that _observers behaves as a defaultdict."""

        # Accessing non-existent key should create empty list
        assert polling_dispatcher._observers["new.event"] == []
        assert isinstance(polling_dispatcher._observers["new.event"], list)

    @patch("midil.infrastructure.messaging.dispatchers.polling.logger")
    async def test_notify_logging_messages(self, mock_logger, polling_dispatcher):
        """Test specific logging messages in _notify."""

        async def test_observer(event: str, body: Dict[str, Any]):
            pass

        polling_dispatcher.register("log.test", test_observer)

        with patch("anyio.create_task_group") as mock_create_task_group:
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("log.test", {"test": "body"})

        # Check debug message about processing event
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Processing event 'log.test'" in msg for msg in debug_calls)

    def test_type_annotations(self):
        """Test type annotations are properly defined."""

        # Test Observer type union
        assert hasattr(Observer, "__args__")  # Union type should have __args__

        # Test that FunctionalObserver and MethodObserver are properly typed
        import typing

        if hasattr(typing, "get_args"):  # Python 3.8+
            args = typing.get_args(Observer)
            assert FunctionalObserver in args
            assert MethodObserver in args

    async def test_integration_with_decorator_and_notify(self, polling_dispatcher):
        """Test integration between decorator registration and notification."""

        call_log = []

        @polling_dispatcher.on("integration.test")
        async def handler1(event: str, body: Dict[str, Any]):
            call_log.append(("handler1", event, body))

        @polling_dispatcher.on("integration.test")
        async def handler2(event: str, body: Dict[str, Any]):
            call_log.append(("handler2", event, body))

        test_body = {"integration": True, "data": "test"}

        # Let the real task group run without problematic mocking
        await polling_dispatcher._notify("integration.test", test_body)

        # Give tasks time to complete
        await anyio.sleep(0.01)

        # Both handlers should have been called
        assert len(call_log) == 2
        assert ("handler1", "integration.test", test_body) in call_log
        assert ("handler2", "integration.test", test_body) in call_log

    def test_global_dispatcher_instance(self):
        """Test that global dispatcher instance is available."""
        assert dispatcher is not None
        assert isinstance(dispatcher, PollingEventDispatcher)

    def test_global_dispatcher_singleton_behavior(self):
        """Test that the global dispatcher behaves as expected."""
        from midil.infrastructure.messaging.dispatchers.polling import (
            dispatcher as dispatcher1,
        )
        from midil.infrastructure.messaging.dispatchers.polling import (
            dispatcher as dispatcher2,
        )

        # Should be the same instance
        assert dispatcher1 is dispatcher2

    async def test_complex_event_types(self, polling_dispatcher):
        """Test handling of complex event type names."""

        complex_events = [
            "user.profile.updated",
            "payment.card.expired",
            "system.health.check.failed",
            "api.rate.limit.exceeded",
            "database.connection.restored",
        ]

        handlers = {}
        for event_type in complex_events:

            @polling_dispatcher.on(event_type)
            async def handler(event: str, body: Dict[str, Any]) -> None:
                pass

            handlers[event_type] = handler

        # All should be registered correctly
        for event_type in complex_events:
            assert event_type in polling_dispatcher._observers
            assert len(polling_dispatcher._observers[event_type]) == 1

    async def test_observer_exception_handling(self, polling_dispatcher):
        """Test that exceptions in observers don't break the dispatcher."""

        async def failing_observer(event: str, body: Dict[str, Any]) -> None:
            raise Exception("Observer failed")

        async def working_observer(event: str, body: Dict[str, Any]) -> None:
            pass

        polling_dispatcher.register("exception.test", failing_observer)
        polling_dispatcher.register("exception.test", working_observer)

        # This should not raise an exception
        # The actual exception handling happens in anyio tasks
        with patch("anyio.create_task_group") as mock_create_task_group:
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("exception.test", {})
            assert mock_tg.start_soon.call_count == 2

    def test_inspect_method_detection(self, polling_dispatcher):
        """Test that inspect.ismethod is used correctly."""

        class TestClass:
            async def method_observer(self, event: str, body: Dict[str, Any]) -> None:
                pass

        instance = TestClass()

        # Test that method detection works
        assert inspect.ismethod(instance.method_observer)

        # Function should not be detected as method
        async def function_observer(event: str, body: Dict[str, Any]) -> None:
            pass

        assert not inspect.ismethod(function_observer)

    async def test_empty_body_handling(self, polling_dispatcher):
        """Test handling of empty event bodies."""

        async def test_observer(event: str, body: Dict[str, Any]) -> None:
            assert body == {}

        polling_dispatcher.register("empty.test", test_observer)

        with patch("anyio.create_task_group") as mock_create_task_group:
            mock_tg = Mock()
            mock_context_manager = Mock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_tg)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_create_task_group.return_value = mock_context_manager

            await polling_dispatcher._notify("empty.test", {})
            assert mock_tg.start_soon.call_count == 1
