from midil.event.consumer.strategies.pull import (
    PullEventConsumer,
    PullEventConsumerConfig,
)
import aioboto3
from typing import Optional
import asyncio
from loguru import logger
from midil.event.consumer.strategies.base import Message
from pydantic import Field
from botocore.exceptions import ClientError
from typing import Dict, Any
import json
from datetime import datetime


class SQSConsumerConfig(PullEventConsumerConfig):
    type: str = "sqs"
    dlq_uri: Optional[str] = Field(None, description="URL of the dead-letter queue")
    visibility_timeout: int = Field(
        default=30, description="Visibility timeout in seconds", ge=0
    )
    max_number_of_messages: int = Field(
        default=10, description="Max messages to receive per poll (1-10)", ge=1, le=10
    )
    wait_time_seconds: int = Field(
        default=20, description="Wait time for long polling (0-20)", ge=0, le=20
    )
    poll_interval: float = Field(
        default=0.1, description="Interval between polls if no messages", ge=0.0
    )
    max_concurrent_messages: int = Field(
        default=10, description="Max concurrent messages to process", ge=1
    )
    max_retries: int = Field(default=3, description="Max retries for a message", ge=0)


class SQSConsumer(PullEventConsumer):
    def __init__(
        self,
        config: SQSConsumerConfig,
    ):
        self.config = config
        self.session = aioboto3.Session(
            region_name=self._get_region_from_queue_url(config.endpoint)
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent_messages)

    def _get_region_from_queue_url(self, queue_url: str) -> str:
        # Example: "https://sqs.us-east-1.amazonaws.com/1234567890/example-queue"
        # We want to extract "us-east-1"
        # Split by "//" then by "." and take the second part
        try:
            host = queue_url.split("//", 1)[1].split("/")[
                0
            ]  # e.g. "sqs.us-east-1.amazonaws.com"
            region = host.split(".")[1]  # "us-east-1"
            return region
        except Exception as e:
            logger.error(f"Could not extract region from queue url: {e}")
            raise ValueError(
                f"Could not extract region from queue url: {queue_url}"
            ) from e

    async def ack(self, message: Message) -> None:
        """
        Acknowledge (delete) the message from the SQS queue.

        Args:
            message (EventContext): The SQS message dictionary, expected to contain 'ReceiptHandle'.
        """
        try:
            async with self.session.client("sqs") as sqs:
                await sqs.delete_message(
                    QueueUrl=self.config.endpoint,
                    ReceiptHandle=message.ack_handle,
                )
                logger.debug(f"Acknowledged message {message.id}")
        except ClientError as e:
            logger.error(f"Error acknowledging message {message.id}: {e}")

    async def nack(self, message: Message, requeue: bool = True) -> None:
        """
        Negative acknowledge the message.

        Behavior:
        - If `requeue` is True and a DLQ is configured, the message is explicitly
            sent to the DLQ and then removed from the source queue to avoid duplicates.
        - If `requeue` is False, the message visibility timeout is reset to 0,
            making it immediately available again in the source queue.
        - If no DLQ is configured but the source queue has an SQS redrive policy,
            repeated nacks will eventually cause SQS to move the message to the DLQ
            automatically once `maxReceiveCount` is exceeded.

        Args:
            message (Message): The SQS message object (with ReceiptHandle, Body, etc.).
            requeue (bool): Whether to send the message to the DLQ (if configured).
        """
        try:
            async with self.session.client("sqs") as sqs:
                if requeue and self.config.dlq_uri:
                    # move to dead letter queue
                    await sqs.send_message(
                        QueueUrl=self.config.dlq_uri,
                        MessageBody=message.model_dump_json(),
                        MessageGroupId=message.metadata.get(
                            "MessageGroupId", "default"
                        ),
                        MessageDeduplicationId=message.metadata.get(
                            "MessageDeduplicationId", str(message.id)
                        ),
                    )
                    await self.ack(message)  # Remove from source queue
                    logger.debug(f"Sent message {message.id} to DLQ")

                else:
                    await sqs.change_message_visibility(
                        QueueUrl=self.config.endpoint,
                        ReceiptHandle=message.ack_handle,
                        VisibilityTimeout=0,
                    )
                    logger.debug(f"Reset visibility for message {message.id}")

        except ClientError as e:
            logger.error(f"Error nacking message {message.id}: {e}")

    async def _poll_loop(self) -> None:
        """
        Main loop for polling SQS and processing messages.
        """
        async with self.session.client("sqs") as sqs:
            while self._running:
                for attempt in range(self.config.max_retries + 1):
                    try:
                        response = await sqs.receive_message(
                            QueueUrl=self.config.endpoint,
                            MaxNumberOfMessages=self.config.max_number_of_messages,
                            VisibilityTimeout=self.config.visibility_timeout,
                            WaitTimeSeconds=self.config.wait_time_seconds,
                            AttributeNames=["All"],
                            MessageAttributeNames=["All"],
                        )
                        messages = response.get("Messages", [])
                        if messages:
                            # Process messages in parallel with semaphore
                            logger.debug(
                                f"Found {len(messages)} message(s), dispatching..."
                            )
                            tasks = [self._process_message(msg) for msg in messages]
                            await asyncio.gather(*tasks)
                        else:
                            await asyncio.sleep(self.config.poll_interval)
                        break  # Success, exit retry loop
                    except ClientError as e:
                        logger.error(
                            f"Error polling SQS (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}"
                        )
                        if attempt == self.config.max_retries:
                            logger.critical("Exhausted retries, stopping consumer")
                            await self.stop()
                            break
                        await asyncio.sleep(self.config.poll_interval)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Parse and dispatch a single message to subscribers.
        """
        async with self._semaphore:
            try:
                try:
                    body = json.loads(message["Body"])
                except json.JSONDecodeError:
                    body = message["Body"]

                # Convert SentTimestamp to datetime
                sent_timestamp = message.get("Attributes", {}).get("SentTimestamp")
                timestamp = (
                    datetime.fromtimestamp(int(sent_timestamp) / 1000)
                    if sent_timestamp
                    else None
                )

                # Combine Attributes and MessageAttributes for metadata
                metadata = {
                    **message.get("Attributes", {}),
                    **message.get("MessageAttributes", {}),
                }
                print("Hi")

                event = Message(
                    id=message["MessageId"],
                    body=body,
                    timestamp=timestamp,
                    ack_handle=message["ReceiptHandle"],
                    source="sqs",
                    metadata=metadata,
                )
                await self.dispatch(event)

            except Exception as e:
                logger.error(
                    f"Error processing message {message.get('MessageId')}: {e}"
                )
                await self.nack(event, requeue=True)
