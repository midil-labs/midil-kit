from __future__ import annotations

import aioboto3
from typing import Any, Dict, List, Optional, Sequence, cast, Protocol
import asyncio

from midil.event.consumer.queues.base import EventQueue


class SQSClient(Protocol):
    async def receive_message(self, **kwargs: Any) -> Dict[str, Any]:
        ...

    async def delete_message_batch(self, **kwargs: Any) -> Dict[str, Any]:
        ...

    async def change_message_visibility(self, **kwargs: Any) -> Dict[str, Any]:
        ...


class SQSEventQueue(EventQueue):
    """
    SQS-backed EventQueue with client reuse and batch delete support. Use as a long-lived object.
    """

    def __init__(
        self,
        queue_url: str,
        region_name: Optional[str] = None,
        session: Optional[aioboto3.Session] = None,
    ):
        self.queue_url = queue_url
        self._session = session or aioboto3.Session(region_name=region_name)
        self._client_cm: Optional[Any] = None
        self._client: Optional[SQSClient] = None
        self._shutdown = asyncio.Event()

    async def _ensure_client(self) -> None:
        if self._client is None:
            # Maintain the context manager to close it later
            self._client_cm = self._session.client("sqs")
            client = await self._client_cm.__aenter__()
            # Narrow runtime client to the protocol for typing
            self._client = cast(SQSClient, client)

    async def receive_messages(
        self,
        max_messages: int = 10,
        wait_time: int = 20,
        visibility_timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        await self._ensure_client()
        assert self._client is not None, "Client not initialized"
        params: Dict[str, Any] = {
            "QueueUrl": self.queue_url,
            "MaxNumberOfMessages": max_messages,
            "WaitTimeSeconds": wait_time,
        }
        if visibility_timeout is not None:
            params["VisibilityTimeout"] = visibility_timeout

        resp = await self._client.receive_message(**params)
        return resp.get("Messages", [])

    async def delete_messages_batch(self, receipt_handles: Sequence[str]) -> None:
        if not receipt_handles:
            return
        await self._ensure_client()
        assert self._client is not None
        entries = [
            {"Id": str(i), "ReceiptHandle": rh} for i, rh in enumerate(receipt_handles)
        ]
        for i in range(0, len(entries), 10):
            chunk = entries[i : i + 10]
            await self._client.delete_message_batch(
                QueueUrl=self.queue_url, Entries=chunk
            )

    async def change_message_visibility(
        self, receipt_handle: str, visibility_timeout: int
    ) -> None:
        await self._ensure_client()
        assert self._client is not None, "Client not initialized"
        await self._client.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=visibility_timeout,
        )

    async def close(self) -> None:
        if self._client_cm is not None:
            try:
                await self._client_cm.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                self._client_cm = None
                self._client = None
        self._shutdown.set()
