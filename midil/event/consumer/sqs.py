# import aioboto3
# import asyncio
# from typing import Any, Dict, Protocol, List, Self, cast
# from pydantic import Field
# from botocore.exceptions import ClientError
# from midil.event.consumer.base import (
#     EventConsumer,
#     Message,
#     EventConsumerConfig,
#     EventContext,
#     Subscriber,
# )


# class SQSConsumerConfig(EventConsumerConfig):
#     """
#     Configuration for SQS event consumer.
#     """

#     type: str = "sqs"
#     queue_url: str = Field(..., description="The URL of the SQS queue")
#     region_name: str = Field(default="us-east-1", description="AWS region")
#     visibility_timeout: int = Field(
#         default=30, description="Visibility timeout in seconds"
#     )
#     max_number_of_messages: int = Field(
#         default=10, description="Max messages to receive per poll (1-10)"
#     )
#     wait_time_seconds: int = Field(
#         default=20, description="Wait time for long polling (0-20)"
#     )
#     poll_interval: float = Field(
#         default=1.0, description="Interval between polls if no messages"
#     )


# class SQSClient(Protocol):
#     async def receive_message(self, **kwargs: Any) -> Dict[str, Any]:
#         ...

#     async def delete_message(self, **kwargs: Any) -> Dict[str, Any]:
#         ...

#     async def change_message_visibility(self, **kwargs: Any) -> Dict[str, Any]:
#         ...

#     async def __aenter__(self) -> Self:
#         return self

#     async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
#         pass


# class SQSConsumer(EventConsumer):
#     """
#     SQS implementation of EventConsumer with parallel processing using aioboto3.

#     Polls an SQS queue, dispatches messages to handlers based on the 'type' field,
#     and processes messages concurrently using asyncio.gather.

#     Assumptions:
#     - Messages are JSON with a 'type' key (str) and optional 'payload' (dict).
#     - AWS credentials are configured via environment variables or aioboto3 defaults.
#     - Parallelism: Up to max_number_of_messages processed concurrently per batch.
#     """

#     def __init__(self, config: SQSConsumerConfig):
#         self._config: SQSConsumerConfig = config  # type hinting support
#         EventConsumer.__init__(self, config)
#         self._session = aioboto3.Session()
#         self._sqs_client: SQSClient | None = None
#         self._running: bool = False
#         self._loop_task: asyncio.Task[Any] | None = None

#     @property
#     def config(self) -> SQSConsumerConfig:
#         return self._config

#     @property
#     async def sqs_client(self) -> SQSClient:
#         if self._sqs_client is None:
#             self._sqs_client = await self._session.client(
#                 "sqs", region_name=self._config.region_name
#             ).__aenter__()
#         client = cast(SQSClient, self._sqs_client)
#         return client

#     async def subscribe(self, event_type: str, handler: Subscriber) -> None:
#         """
#         Register a handler for an event type.
#         """
#         await super().subscribe(event_type, handler)

#     async def start(self) -> None:
#         """
#         Start the consumption loop in a background task.
#         """
#         if self._running:
#             return
#         self._sqs_client = await self.sqs_client
#         self._running = True
#         self._loop_task = asyncio.create_task(self._consumption_loop())

#     async def close(self) -> None:
#         """
#         Stop the consumption loop, close the client, and wait for the task to complete.
#         """
#         if not self._running:
#             return
#         self._running = False
#         if self._loop_task:
#             await self._loop_task
#             self._loop_task = None
#         if self._sqs_client:
#             await self._sqs_client.__aexit__(None, None, None)
#             self._sqs_client = None

#     async def _consume(self) -> List[EventContext]:
#         """
#         Main loop for polling SQS and processing messages.
#         """
#         try:
#             sqs = await self.sqs_client
#             response = await sqs.receive_message(
#                 QueueUrl=self._config.queue_url,
#                 MaxNumberOfMessages=self._config.max_number_of_messages,
#                 VisibilityTimeout=self._config.visibility_timeout,
#                 WaitTimeSeconds=self._config.wait_time_seconds,
#             )
#             messages = response.get("Messages", [])
#             if messages:
#                 # Convert each message dict to an EventContext (or compatible type)
#                 # If Message is not a subclass of EventContext, convert appropriately
#                 return [cast(EventContext, Message(**message)) for message in messages]
#             else:
#                 await asyncio.sleep(self._config.poll_interval)
#                 return []
#         except ClientError as e:
#             print(f"Error polling SQS: {e}")
#             return []

#     async def ack(self, message: Message) -> None:
#         """
#         Acknowledge by deleting the message.
#         """
#         try:
#             sqs = await self.sqs_client
#             await sqs.delete_message(
#                 QueueUrl=self._config.queue_url, ReceiptHandle=message["ReceiptHandle"]
#             )
#         except ClientError as e:
#             print(f"Error acknowledging message {message['MessageId']}: {e}")

#     async def nack(self, message: Dict[str, Any], requeue: bool = True) -> None:
#         """
#         Negative acknowledge: reset visibility if requeue, else delete.
#         """
#         try:
#             if requeue:
#                 await self._sqs_client.change_message_visibility(
#                     QueueUrl=self._config.queue_url,
#                     ReceiptHandle=message["ReceiptHandle"],
#                     VisibilityTimeout=0,
#                 )
#             else:
#                 await self._sqs_client.delete_message(
#                     QueueUrl=self._config.queue_url,
#                     ReceiptHandle=message["ReceiptHandle"],
#                 )
#         except ClientError as e:
#             print(f"Error nacking message {message['MessageId']}: {e}")
