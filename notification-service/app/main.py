import asyncio
import json
import os
from datetime import datetime

import aio_pika
from fastapi import FastAPI
from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notifications.db")
EXCHANGE_NAME = "events"
QUEUE_NAME = "notification.payment.events"


class Base(DeclarativeBase):
    pass


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, nullable=False)
    customer_email: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
app = FastAPI(title="Notification Service")


async def consume_payment_events() -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key="payment.completed")
    await queue.bind(exchange, routing_key="payment.failed")

    async with queue.iterator() as queue_iter:
        async for incoming in queue_iter:
            async with incoming.process():
                event = json.loads(incoming.body.decode("utf-8"))

                is_success = event["event_type"] == "payment.completed"
                text = (
                    f"Payment successful for order {event['order_id']}"
                    if is_success
                    else f"Payment failed for order {event['order_id']}: {event.get('reason', 'unknown reason')}"
                )

                record = Notification(
                    id=f"{event['order_id']}:{event['event_type']}",
                    order_id=event["order_id"],
                    customer_email=event["customer_email"],
                    status=event["event_type"],
                    message=text,
                )

                with Session(engine) as session:
                    session.merge(record)
                    session.commit()

                print(text, flush=True)


@app.on_event("startup")
async def startup() -> None:
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(consume_payment_events())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
