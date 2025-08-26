# from typing import Optional
# from midil.event.producer.base import EventProducer
# import aioboto3


# class SQSProducer(EventProducer):
#     def __init__(
#         self,
#         queue_url: str,
#         region_name: Optional[str] = None,
#         session: Optional[aioboto3.Session] = None,
#     ):
#         self.queue_url = queue_url
#         self._session = session or aioboto3.Session(region_name=region_name)
#         self._client_cm: Optional[Any] = None
#         self._client: Optional[SQSClient] = None
#         self._shutdown = asyncio.Event()

#     async def _ensure_client(self) -> None:
#         if self._client is None:
#             # Maintain the context manager to close it later
#             self._client_cm = self._session.client("sqs")
