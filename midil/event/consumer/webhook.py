from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from midil.event.consumer.strategies.base import Message
from midil.event.consumer.strategies.push import (
    PushEventConsumer,
    PushEventConsumerConfig,
)


class WebhookPushConsumerConfig(PushEventConsumerConfig):
    type: str = "webhook"
    endpoint: str = "/events"


class WebhookPushConsumer(PushEventConsumer):
    def __init__(self, config: WebhookPushConsumerConfig):
        super().__init__(config)
        self._config: WebhookPushConsumerConfig = config
        self._router = APIRouter()

        logger.info("Starting webhook consumer")

        # Create the route statically so it's available for FastAPI's OpenAPI schema.
        # FastAPI needs to know about all routes at startup time to include them in the OpenAPI schema that powers the Swagger UI
        @self._router.post(
            self._config.endpoint,
            summary="Receive webhook events",
            description="Endpoint to receive webhook events",
        )
        async def receive_hook(request: Request):
            return await self._handler(request)

        logger.info(f"Webhook consumer ready at {self._config.endpoint}")

    @property
    def entrypoint(self) -> APIRouter:
        return self._router

    async def _handler(
        self,
        request: Request,
    ):
        try:
            data: Message = await request.json()
            await self.dispatch(data)
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Webhook event handling failed")
            raise HTTPException(status_code=400, detail=str(e))

    async def start(self) -> None:
        """
        Setup the webhook consumer routes to receive events.
        """
        logger.info(f"Webhook consumer ready at {self._config.endpoint}")

    async def stop(self) -> None:
        self._subscribers.clear()
        logger.info("Webhook consumer stopped")

    # push mode → ack/nack can be no-ops
    async def ack(self, message: Message) -> None:
        logger.debug(f"Acked event {message.id}")

    async def nack(self, message: Message, requeue: bool = True) -> None:
        logger.warning(f"Nacked event {message.id}, requeue={requeue}")
