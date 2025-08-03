# """
# Tests for midil.infrastructure.messaging.consumers.sqs
# """
# import pytest
# import asyncio
# import json
# from unittest.mock import AsyncMock, Mock, patch, MagicMock
# from json import JSONDecodeError

# # Mark all async tests in this module to use anyio
# pytestmark = pytest.mark.anyio

# from midil.infrastructure.messaging.consumers.sqs import (
#     SQSEventConsumer,
#     SQSConsumerException,
#     run_sqs_consumer,
# )


# class TestSQSEventConsumer:
#     """Tests for SQSEventConsumer class."""

#     @pytest.fixture
#     def consumer(self):
#         """Create an SQSEventConsumer instance for testing."""
#         return SQSEventConsumer(
#             queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
#             region_name="us-east-1",
#             max_retries=3
#         )

#     def test_init(self, consumer):
#         """Test SQSEventConsumer initialization."""
#         assert consumer.queue_url == "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
#         assert consumer.region_name == "us-east-1"
#         assert consumer.max_retries == 3
#         assert not consumer._shutdown

#     def test_init_default_max_retries(self):
#         """Test default max_retries value."""
#         consumer = SQSEventConsumer(
#             queue_url="https://test-queue.com",
#             region_name="us-west-2"
#         )
#         assert consumer.max_retries == 3

#     def test_shutdown(self, consumer):
#         """Test shutdown method sets shutdown flag."""
#         assert not consumer._shutdown
#         consumer.shutdown()
#         assert consumer._shutdown

#     async def test_poll_single_message(self, consumer, mock_sqs_message):
#         """Test polling and yielding a single message."""
#         mock_client = AsyncMock()
#         mock_response = {
#             "Messages": [mock_sqs_message]
#         }
#         mock_client.receive_message.return_value = mock_response

#         # Mock the session and client creation
#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         # Set shutdown after one iteration
#         consumer._shutdown = False

#         messages = []
#         async for message, receipt_handle in consumer.poll():
#             messages.append((message, receipt_handle))
#             consumer.shutdown()  # Stop after first message
#             break

#         assert len(messages) == 1
#         message, receipt_handle = messages[0]
#         assert message == {"event": "test.event", "body": {"test": "data"}}
#         assert receipt_handle == "test-receipt-handle"

#     async def test_poll_multiple_messages(self, consumer):
#         """Test polling multiple messages in one batch."""
#         mock_client = AsyncMock()

#         messages = []
#         for i in range(3):
#             msg = {
#                 "Body": f'{{"event": "test.event.{i}", "body": {{"test": "data{i}"}}}}',
#                 "ReceiptHandle": f"receipt-{i}",
#                 "MessageId": f"msg-{i}",
#             }
#             messages.append(msg)

#         mock_response = {"Messages": messages}
#         mock_client.receive_message.return_value = mock_response

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         results = []
#         async for message, receipt_handle in consumer.poll():
#             results.append((message, receipt_handle))
#             if len(results) == 3:
#                 consumer.shutdown()
#                 break

#         assert len(results) == 3
#         for i, (message, receipt_handle) in enumerate(results):
#             assert message["event"] == f"test.event.{i}"
#             assert receipt_handle == f"receipt-{i}"

#     async def test_poll_empty_response(self, consumer):
#         """Test polling when no messages are available."""
#         mock_client = AsyncMock()
#         mock_client.receive_message.return_value = {"Messages": []}

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         # Should not yield anything and eventually timeout/shutdown
#         messages = []
#         consumer.shutdown()  # Shutdown immediately to avoid infinite loop

#         async for message, receipt_handle in consumer.poll():
#             messages.append((message, receipt_handle))

#         assert len(messages) == 0

#     async def test_poll_invalid_json_message(self, consumer):
#         """Test handling of invalid JSON messages."""
#         mock_client = AsyncMock()

#         invalid_msg = {
#             "Body": "invalid json content",
#             "ReceiptHandle": "invalid-receipt",
#             "MessageId": "invalid-msg",
#         }

#         mock_response = {"Messages": [invalid_msg]}
#         mock_client.receive_message.return_value = mock_response
#         mock_client.delete_message.return_value = None

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             messages = []

#             async for message, receipt_handle in consumer.poll():
#                 messages.append((message, receipt_handle))
#                 consumer.shutdown()  # Stop after processing first message
#                 break

#             # Should not yield any messages (invalid JSON should be filtered out)
#             assert len(messages) == 0

#             # Should log error and delete the invalid message
#             mock_logger.error.assert_called()
#             mock_client.delete_message.assert_called_once()

#     def test_is_valid_message(self, consumer):
#         """Test message validation."""
#         # Valid message
#         valid_msg = {"event": "test.event", "body": {"data": "test"}}
#         assert consumer._is_valid_message(valid_msg)

#         # Missing event
#         invalid_msg1 = {"body": {"data": "test"}}
#         assert not consumer._is_valid_message(invalid_msg1)

#         # Missing body
#         invalid_msg2 = {"event": "test.event"}
#         assert not consumer._is_valid_message(invalid_msg2)

#         # Empty dict
#         assert not consumer._is_valid_message({})

#     async def test_delete_message_success(self, consumer):
#         """Test successful message deletion."""
#         mock_client = AsyncMock()
#         mock_client.delete_message.return_value = None

#         await consumer._delete_message(mock_client, "test-receipt-handle")

#         mock_client.delete_message.assert_called_once_with(
#             QueueUrl=consumer.queue_url,
#             ReceiptHandle="test-receipt-handle"
#         )

#     async def test_delete_message_missing_receipt_handle(self, consumer):
#         """Test deletion with missing receipt handle."""
#         mock_client = AsyncMock()

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             await consumer._delete_message(mock_client, None)

#             # Should not call delete_message
#             mock_client.delete_message.assert_not_called()

#             # Should log warning
#             mock_logger.warning.assert_called_once()

#     async def test_delete_message_error(self, consumer):
#         """Test deletion with client error."""
#         mock_client = AsyncMock()
#         mock_client.delete_message.side_effect = Exception("Delete failed")

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             await consumer._delete_message(mock_client, "test-receipt")

#             mock_logger.error.assert_called()

#     async def test_poll_connection_retry(self, consumer):
#         """Test connection retry logic."""
#         mock_session = MagicMock()

#         # First attempt fails, second succeeds
#         side_effect_calls = [
#             Exception("Connection failed"),
#             MagicMock()
#         ]

#         mock_session.create_client.side_effect = side_effect_calls
#         consumer.session = mock_session

#         with patch('asyncio.sleep') as mock_sleep:
#             consumer.shutdown()  # Shutdown to avoid infinite loop

#             async for message, receipt_handle in consumer.poll():
#                 break  # Exit immediately

#             # Should have attempted retry
#             assert mock_session.create_client.call_count >= 1

#     async def test_poll_max_retries_exceeded(self, consumer):
#         """Test behavior when max retries are exceeded."""
#         mock_session = MagicMock()
#         mock_session.create_client.side_effect = Exception("Persistent failure")
#         consumer.session = mock_session

#         with pytest.raises(SQSConsumerException, match="retry limit exceeded"):
#             async for message, receipt_handle in consumer.poll():
#                 break

#     async def test_poll_receive_message_parameters(self, consumer):
#         """Test that receive_message is called with correct parameters."""
#         mock_client = AsyncMock()
#         mock_client.receive_message.return_value = {"Messages": []}

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         consumer.shutdown()  # Shutdown to avoid infinite loop

#         async for message, receipt_handle in consumer.poll():
#             break

#         mock_client.receive_message.assert_called_with(
#             QueueUrl=consumer.queue_url,
#             WaitTimeSeconds=20,
#             MaxNumberOfMessages=10,
#             AttributeNames=["All"],
#             MessageAttributeNames=["All"]
#         )

#     async def test_poll_cancellation(self, consumer):
#         """Test poll cancellation handling."""
#         mock_client = AsyncMock()
#         mock_client.receive_message.side_effect = asyncio.CancelledError()

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             async for message, receipt_handle in consumer.poll():
#                 break

#             mock_logger.info.assert_called_with("Polling cancelled.")

#     async def test_poll_invalid_message_deletion(self, consumer):
#         """Test that invalid messages are deleted."""
#         mock_client = AsyncMock()

#         invalid_message = {
#             "Body": '{"invalid": "message"}',  # Missing required fields
#             "ReceiptHandle": "invalid-receipt",
#             "MessageId": "invalid-id"
#         }

#         mock_response = {"Messages": [invalid_message]}
#         mock_client.receive_message.return_value = mock_response

#         mock_session = MagicMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_session.create_client.return_value = mock_session_context
#         consumer.session = mock_session

#         consumer.shutdown()

#         async for message, receipt_handle in consumer.poll():
#             pass

#         # Invalid message should be deleted
#         mock_client.delete_message.assert_called_once()


# class TestRunSQSConsumer:
#     """Tests for run_sqs_consumer function."""

#     @pytest.fixture
#     def mock_consumer(self):
#         """Create a mock consumer for testing."""
#         consumer = Mock(spec=SQSEventConsumer)
#         consumer.poll.return_value = AsyncMock()
#         consumer.session = Mock()
#         mock_client = AsyncMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         consumer.session.create_client.return_value = mock_session_context
#         return consumer

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     @patch('midil.infrastructure.messaging.consumers.sqs.event_context')
#     @patch('midil.infrastructure.messaging.consumers.sqs.dispatcher')
#     async def test_run_sqs_consumer_success(self, mock_dispatcher, mock_event_context, mock_consumer_class):
#         """Test successful message processing."""
#         # Setup mocks
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer

#         test_message = {
#             "event": "test.event",
#             "body": {"test": "data"}
#         }

#         # Mock async generator for poll
#         async def mock_poll():
#             yield test_message, "receipt-handle"

#         mock_consumer.poll.return_value = mock_poll()

#         # Mock context manager
#         mock_context = Mock()
#         mock_context.id = "test-context-id"
#         mock_event_context.return_value.__aenter__.return_value = mock_context

#         # Mock dispatcher
#         mock_dispatcher.notify = AsyncMock()

#         # Mock session for deletion
#         mock_client = AsyncMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_consumer.session.create_client.return_value = mock_session_context

#         # Run consumer (with a way to stop it)
#         task = asyncio.create_task(run_sqs_consumer("test-queue", "us-east-1"))
#         await asyncio.sleep(0.1)  # Let it process one message
#         task.cancel()

#         try:
#             await task
#         except asyncio.CancelledError:
#             pass

#         # Verify message was processed
#         mock_dispatcher.notify.assert_called_once_with("test.event", {"test": "data"})

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     @patch('midil.infrastructure.messaging.consumers.sqs.event_context')
#     @patch('midil.infrastructure.messaging.consumers.sqs.dispatcher')
#     async def test_run_sqs_consumer_processing_error(self, mock_dispatcher, mock_event_context, mock_consumer_class):
#         """Test handling of message processing errors."""
#         # Setup mocks
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer

#         test_message = {
#             "event": "error.event",
#             "body": {"will": "fail"}
#         }

#         async def mock_poll():
#             yield test_message, "receipt-handle"

#         mock_consumer.poll.return_value = mock_poll()

#         # Mock context manager
#         mock_context = Mock()
#         mock_context.id = "error-context-id"
#         mock_event_context.return_value.__aenter__.return_value = mock_context

#         # Make dispatcher fail
#         mock_dispatcher.notify = AsyncMock(side_effect=Exception("Processing failed"))

#         # Mock session
#         mock_client = AsyncMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_consumer.session.create_client.return_value = mock_session_context

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             task = asyncio.create_task(run_sqs_consumer("test-queue", "us-east-1"))
#             await asyncio.sleep(0.1)
#             task.cancel()

#             try:
#                 await task
#             except asyncio.CancelledError:
#                 pass

#             # Should log the exception
#             mock_logger.exception.assert_called()

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     async def test_run_sqs_consumer_cancellation(self, mock_consumer_class):
#         """Test consumer cancellation handling."""
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer
#         mock_consumer.poll.side_effect = asyncio.CancelledError()
#         mock_consumer.shutdown = Mock()

#         with patch('midil.infrastructure.messaging.consumers.sqs.logger') as mock_logger:
#             try:
#                 await run_sqs_consumer("test-queue", "us-east-1")
#             except asyncio.CancelledError:
#                 pass

#             mock_logger.info.assert_any_call("SQS consumer task cancelled.")
#             mock_consumer.shutdown.assert_called_once()

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     async def test_run_sqs_consumer_critical_error(self, mock_consumer_class):
#         """Test handling of critical consumer errors."""
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer
#         mock_consumer.poll.side_effect = Exception("Critical failure")
#         mock_consumer.shutdown = Mock()

#         with pytest.raises(Exception, match="Critical failure"):
#             await run_sqs_consumer("test-queue", "us-east-1")

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     async def test_run_sqs_consumer_message_deletion_on_success(self, mock_consumer_class):
#         """Test that messages are deleted after successful processing."""
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer

#         test_message = {
#             "event": "success.event",
#             "body": {"success": True}
#         }

#         async def mock_poll():
#             yield test_message, "success-receipt"

#         mock_consumer.poll.return_value = mock_poll()
#         mock_consumer._delete_message = AsyncMock()

#         # Mock session
#         mock_client = AsyncMock()
#         mock_session_context = AsyncMock()
#         mock_session_context.__aenter__.return_value = mock_client
#         mock_session_context.__aexit__.return_value = None
#         mock_consumer.session.create_client.return_value = mock_session_context

#         with patch('midil.infrastructure.messaging.consumers.sqs.event_context'):
#             with patch('midil.infrastructure.messaging.consumers.sqs.dispatcher') as mock_dispatcher:
#                 mock_dispatcher.notify = AsyncMock()

#                 task = asyncio.create_task(run_sqs_consumer("test-queue", "us-east-1"))
#                 await asyncio.sleep(0.1)
#                 task.cancel()

#                 try:
#                     await task
#                 except asyncio.CancelledError:
#                     pass

#         # Message should be deleted after successful processing
#         mock_consumer._delete_message.assert_called_once_with(mock_client, "success-receipt")

#     @patch('midil.infrastructure.messaging.consumers.sqs.SQSEventConsumer')
#     async def test_run_sqs_consumer_no_deletion_on_failure(self, mock_consumer_class):
#         """Test that messages are not deleted after processing failure."""
#         mock_consumer = Mock()
#         mock_consumer_class.return_value = mock_consumer

#         test_message = {
#             "event": "fail.event",
#             "body": {"will": "fail"}
#         }

#         async def mock_poll():
#             yield test_message, "fail-receipt"

#         mock_consumer.poll.return_value = mock_poll()
#         mock_consumer._delete_message = AsyncMock()

#         with patch('midil.infrastructure.messaging.consumers.sqs.event_context'):
#             with patch('midil.infrastructure.messaging.consumers.sqs.dispatcher') as mock_dispatcher:
#                 mock_dispatcher.notify = AsyncMock(side_effect=Exception("Processing failed"))

#                 task = asyncio.create_task(run_sqs_consumer("test-queue", "us-east-1"))
#                 await asyncio.sleep(0.1)
#                 task.cancel()

#                 try:
#                     await task
#                 except asyncio.CancelledError:
#                     pass

#         # Message should NOT be deleted after failed processing
#         mock_consumer._delete_message.assert_not_called()


# class TestSQSConsumerException:
#     """Tests for SQSConsumerException."""

#     def test_exception_inheritance(self):
#         """Test that SQSConsumerException inherits from Exception."""
#         assert issubclass(SQSConsumerException, Exception)

#     def test_exception_instantiation(self):
#         """Test exception instantiation."""
#         exc = SQSConsumerException("Test error")
#         assert str(exc) == "Test error"

#     def test_exception_can_be_raised(self):
#         """Test that exception can be raised and caught."""
#         with pytest.raises(SQSConsumerException, match="Test message"):
#             raise SQSConsumerException("Test message")
