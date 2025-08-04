import asyncio
import json
from typing import AsyncGenerator, Optional, Dict, Any

from aiobotocore.session import get_session
from json import JSONDecodeError
from loguru import logger

from midil.event.context import event_context
from midil.event.dispatchers.polling import dispatcher


class SQSConsumerException(Exception):
    """Raised when the SQS consumer fails to initialize or poll."""


class SQSEventConsumer:
    def __init__(self, queue_url: str, region_name: str, max_retries: int = 3):
        self.queue_url = queue_url
        self.region_name = region_name
        self.max_retries = max_retries
        self.session = get_session()
        self._shutdown = False

    def shutdown(self) -> None:
        """Signals the consumer to stop polling."""
        logger.info("Shutdown signal received for SQS consumer.")
        self._shutdown = True

    async def poll(self) -> AsyncGenerator[tuple[Dict[str, Any], str], None]:
        """Continuously poll SQS for messages and yield them with their receipt handles."""
        retries = 0

        while not self._shutdown:
            try:
                async with self.session.create_client(
                    "sqs", region_name=self.region_name
                ) as client:
                    retries = 0  # Reset retry count on successful connection

                    while not self._shutdown:
                        try:
                            response = await client.receive_message(
                                QueueUrl=self.queue_url,
                                WaitTimeSeconds=20,
                                MaxNumberOfMessages=10,
                                AttributeNames=["All"],
                                MessageAttributeNames=["All"],
                            )
                            messages = response.get("Messages", [])
                            logger.debug(f"Polled {len(messages)} message(s) from SQS.")

                            for msg in messages:
                                receipt_handle = msg.get("ReceiptHandle")
                                try:
                                    body = json.loads(msg["Body"])
                                    if not self._is_valid_message(body):
                                        logger.warning(
                                            f"Invalid message format: {body}"
                                        )
                                        await self._delete_message(
                                            client, receipt_handle
                                        )
                                        continue

                                    yield body, receipt_handle

                                except (JSONDecodeError, KeyError) as e:
                                    logger.error(
                                        f"Malformed message: {msg.get('Body')} - {e}"
                                    )
                                    await self._delete_message(client, receipt_handle)
                                except Exception as e:
                                    logger.exception(
                                        f"Unhandled error parsing message: {e}"
                                    )
                                    # Do not delete to allow retry
                        except asyncio.CancelledError:
                            logger.info("Polling cancelled.")
                            return
                        except Exception as e:
                            logger.error(f"Polling error: {e}")
                            await asyncio.sleep(min(2**retries, 30))
                            break  # Recreate the client session after a sleep

            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    logger.critical(f"SQS connection failed after {retries} attempts.")
                    raise SQSConsumerException(
                        "SQS connection retry limit exceeded."
                    ) from e

                backoff = min(2**retries, 60)
                logger.warning(f"Retrying SQS connection in {backoff}s due to: {e}")
                await asyncio.sleep(backoff)

    async def _delete_message(self, client: Any, receipt_handle: Optional[str]) -> None:
        """Delete a message from SQS if the receipt handle is valid."""
        if not receipt_handle:
            logger.warning("Attempted to delete message with missing receipt handle.")
            return

        try:
            await client.delete_message(
                QueueUrl=self.queue_url, ReceiptHandle=receipt_handle
            )
            logger.debug("Message deleted from SQS.")
        except Exception as e:
            logger.error(f"Failed to delete message from SQS: {e}")

    def _is_valid_message(self, body: Dict[str, Any]) -> bool:
        """Validate that the message has the required fields."""
        return "event" in body and "body" in body


async def run_sqs_consumer(queue_url: str, region_name: str) -> None:
    """Start the SQS consumer and process messages with retry and context handling."""
    consumer = SQSEventConsumer(queue_url=queue_url, region_name=region_name)

    try:
        logger.info(f"Starting SQS consumer for queue: {queue_url}")

        async for message, receipt_handle in consumer.poll():
            success = False
            try:
                async with event_context(message["event"]) as ctx:
                    logger.debug(
                        f"Processing event: {message['event']} with context ID: {ctx.id}"
                    )
                    await dispatcher.notify(message["event"], message["body"])
                    success = True
                    logger.debug(f"Successfully processed event: {message['event']}")
            except Exception as e:
                logger.exception(
                    f"Failed to process event: {message.get('event')}: {e}"
                )
                # Message will be retried by SQS

            if success:
                async with consumer.session.create_client(
                    "sqs", region_name=region_name
                ) as client:
                    await consumer._delete_message(client, receipt_handle)

    except asyncio.CancelledError:
        logger.info("SQS consumer task cancelled.")
        consumer.shutdown()
    except Exception as e:
        logger.critical(f"SQS consumer crashed: {e}")
        raise
    finally:
        logger.info("SQS consumer shutdown complete.")
