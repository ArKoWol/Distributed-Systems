import asyncio
import json
import os
import random

import aio_pika
from fastapi import FastAPI


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_NAME = "events"
QUEUE_NAME = "payment.order.created"

app = FastAPI(title="Payment Service")


async def process_payment(order_event: dict) -> dict:
    await asyncio.sleep(1.0)
    is_success = random.random() > 0.2
    return {
        "event_type": "payment.completed" if is_success else "payment.failed",
        "order_id": order_event["order_id"],
        "customer_email": order_event["customer_email"],
        "item_name": order_event["item_name"],
        "amount": order_event["amount"],
        "reason": None if is_success else "Insufficient funds (simulated)",
    }


async def consume_orders() -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key="order.created")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                order_event = json.loads(message.body.decode("utf-8"))
                payment_event = await process_payment(order_event)

                await exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(payment_event).encode("utf-8"),
                        content_type="application/json",
                    ),
                    routing_key=payment_event["event_type"],
                )


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(consume_orders())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
