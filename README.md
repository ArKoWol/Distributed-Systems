# Homework 2 - Event-Driven Microservices (Variant 2)

This project implements an Online Order Processing System with asynchronous event-driven communication using FastAPI and RabbitMQ.

## Services

1. **Order Service** (`POST /orders`, `GET /orders/{id}`)
   - Stores orders in SQLite
   - Publishes `order.created`
2. **Payment Service**
   - Consumes `order.created`
   - Simulates payment and publishes `payment.completed` or `payment.failed`
3. **Notification Service**
   - Consumes payment events
   - Stores notifications in SQLite

## Run with Docker Compose

```bash
docker compose up --build
```

Endpoints:
- Order API: http://localhost:8000/docs
- RabbitMQ UI: http://localhost:15672 (guest/guest)

## Quick test

Create order:

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"student@example.com","item_name":"Laptop","amount":1200}'
```

Get order:

```bash
curl http://localhost:8000/orders/<ORDER_ID>
```

Watch logs for payment and notification:

```bash
docker compose logs -f payment-service notification-service
```
