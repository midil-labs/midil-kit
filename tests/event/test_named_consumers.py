import pytest
from unittest.mock import patch
from midil.settings import (
    get_consumers_by_type,
    get_consumer_event_settings,
    EventSettingsError,
)
from midil.event.config import EventConfig, EventConsumerType
from midil.event.consumer.sqs import SQSConsumerEventConfig
from midil.event.consumer.webhook import WebhookConsumerEventConfig


class TestNamedConsumers:
    """Test named consumer configuration functionality."""

    def test_get_consumer_by_name(self):
        """Test getting a specific consumer by name."""
        mock_event_config = EventConfig(
            consumers={
                "booking_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
                ),
                "payment_webhook": WebhookConsumerEventConfig(
                    endpoint="/webhook/payments"
                ),
            }
        )

        with patch("midil.settings.get_event_settings", return_value=mock_event_config):
            # Test getting SQS consumer
            booking_consumer = get_consumer_event_settings("booking_queue")
            assert booking_consumer.type == "sqs"
            assert (
                booking_consumer.queue_url
                == "https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
            )

            # Test getting webhook consumer
            payment_consumer = get_consumer_event_settings("payment_webhook")
            assert payment_consumer.type == "webhook"
            assert payment_consumer.endpoint == "/webhook/payments"

    def test_get_consumer_by_name_not_found(self):
        """Test error when consumer name is not found."""
        mock_event_config = EventConfig(
            consumers={
                "booking_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
                ),
            }
        )

        with patch("midil.settings.get_event_settings", return_value=mock_event_config):
            with pytest.raises(
                EventSettingsError, match="Consumer 'nonexistent' not found"
            ):
                get_consumer_event_settings("nonexistent")

    def test_get_consumers_by_type_sqs(self):
        """Test getting consumers by type (SQS)."""
        mock_event_config = EventConfig(
            consumers={
                "booking_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
                ),
                "payment_webhook": WebhookConsumerEventConfig(
                    endpoint="/webhook/payments"
                ),
                "notification_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/notification-queue"
                ),
            }
        )

        with patch("midil.settings.get_event_settings", return_value=mock_event_config):
            sqs_consumers = get_consumers_by_type(EventConsumerType.SQS)

            assert len(sqs_consumers) == 2
            assert "booking_queue" in sqs_consumers
            assert "notification_queue" in sqs_consumers
            assert "payment_webhook" not in sqs_consumers
            assert all(consumer.type == "sqs" for consumer in sqs_consumers.values())

    def test_get_consumers_by_type_webhook(self):
        """Test getting consumers by type (Webhook)."""
        mock_event_config = EventConfig(
            consumers={
                "booking_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
                ),
                "payment_webhook": WebhookConsumerEventConfig(
                    endpoint="/webhook/payments"
                ),
                "notification_webhook": WebhookConsumerEventConfig(
                    endpoint="/webhook/notifications"
                ),
            }
        )

        with patch("midil.settings.get_event_settings", return_value=mock_event_config):
            webhook_consumers = get_consumers_by_type(EventConsumerType.WEBHOOK)

            assert len(webhook_consumers) == 2
            assert "payment_webhook" in webhook_consumers
            assert "notification_webhook" in webhook_consumers
            assert "booking_queue" not in webhook_consumers
            assert all(
                consumer.type == "webhook" for consumer in webhook_consumers.values()
            )

    def test_get_consumers_by_type_none_found(self):
        """Test error when no consumers of specified type are found."""
        mock_event_config = EventConfig(
            consumers={
                "booking_queue": SQSConsumerEventConfig(
                    queue_url="https://sqs.us-east-1.amazonaws.com/123456789/booking-queue"
                ),
            }
        )

        with patch("midil.settings.get_event_settings", return_value=mock_event_config):
            with pytest.raises(
                EventSettingsError,
                match="No consumer configurations with type 'EventConsumerType.WEBHOOK'",
            ):
                get_consumers_by_type(EventConsumerType.WEBHOOK)
