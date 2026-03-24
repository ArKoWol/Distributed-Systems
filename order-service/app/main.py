import json
import os
import uuid
from datetime import datetime

import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orders.db")
EXCHANGE_NAME = "events"


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_email: Mapped[str] = mapped_column(String, nullable=False)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrderCreate(BaseModel):
    customer_email: str
    item_name: str
    amount: float = Field(gt=0)


class OrderResponse(BaseModel):
    id: str
    customer_email: str
    item_name: str
    amount: float
    status: str


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
app = FastAPI(title="Order Service")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


async def publish_order_created(order: Order) -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)

        payload = {
            "event_type": "order.created",
            "order_id": order.id,
            "customer_email": order.customer_email,
            "item_name": order.item_name,
            "amount": order.amount,
            "created_at": order.created_at.isoformat(),
        }

        await exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode("utf-8"), content_type="application/json"),
            routing_key="order.created",
        )
    finally:
        await connection.close()


@app.post("/orders", response_model=OrderResponse)
async def create_order(order_data: OrderCreate) -> OrderResponse:
    order = Order(
        id=str(uuid.uuid4()),
        customer_email=order_data.customer_email,
        item_name=order_data.item_name,
        amount=order_data.amount,
        status="created",
    )

    with Session(engine, expire_on_commit=False) as session:
        session.add(order)
        session.commit()

    await publish_order_created(order)

    return OrderResponse(
        id=order.id,
        customer_email=order.customer_email,
        item_name=order.item_name,
        amount=order.amount,
        status=order.status,
    )


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str) -> OrderResponse:
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        customer_email=order.customer_email,
        item_name=order.item_name,
        amount=order.amount,
        status=order.status,
    )
