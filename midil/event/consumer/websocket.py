from fastapi import APIRouter, WebSocket
from midil.event.consumer.strategies.push import (
    PushEventConsumer,
    PushEventConsumerConfig,
)
from midil.event.consumer.strategies.base import Message
from loguru import logger
from typing import List


class WebSocketPushConsumerConfig(PushEventConsumerConfig):
    type: str = "websocket"
    endpoint: str = "/events/ws"


class WebSocketPushConsumer(PushEventConsumer):
    def __init__(self, config: WebSocketPushConsumerConfig):
        self.config: WebSocketPushConsumerConfig = config
        self._router = APIRouter()
        self.connections: List[WebSocket] = []

    @property
    def entrypoint(self) -> APIRouter:
        return self._router

    async def _handler(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        try:
            while True:
                data: Message = await websocket.receive_json()
                await self.dispatch(data)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connections.remove(websocket)

    async def start(self) -> None:
        @self._router.websocket(self.config.endpoint)
        async def websocket_endpoint(websocket: WebSocket) -> None:
            return await self._handler(websocket)

        logger.info(f"WebSocket consumer ready at {self.config.endpoint}")

    async def stop(self) -> None:
        self.connections.clear()

    async def ack(self, message: Message) -> None:
        logger.debug(f"Acked WebSocket event {message.id}")

    async def nack(self, message: Message, requeue: bool = True) -> None:
        logger.warning(f"Nacked WebSocket event {message.id}, requeue={requeue}")
