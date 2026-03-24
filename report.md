# HOMEWORK TASK #2

## Event-Driven Microservices with FastAPI and RabbitMQ

Student: Artsiom Yasiukou  
Teacher: Gintaras Dmitrijev  
Vilnius, 2026

## Table of Contents

1. [Aims and objectives of the homework](#1-aims-and-objectives-of-the-homework)
2. [Work steps](#2-work-steps)
   1. [Step 1: Project architecture](#21-step-1-project-architecture)
   2. [Step 2: Order Service](#22-step-2-order-service)
   3. [Step 3: Payment Service](#23-step-3-payment-service)
   4. [Step 4: Notification Service](#24-step-4-notification-service)
   5. [Step 5: Docker Compose integration and test](#25-step-5-docker-compose-integration-and-test)
3. [Conclusions](#3-conclusions)

## 1 Aims and objectives of the homework

The aim of this homework is to design and implement an event-driven distributed backend system using microservices architecture. The implementation is based on FastAPI and asynchronous messaging with RabbitMQ.

The system must satisfy these objectives:

- Separate responsibilities into independent services.
- Avoid direct synchronous calls between services.
- Exchange data only through events in a message broker.
- Implement required flow: `order.created` -> payment result -> notification.
- Containerize services and infrastructure using Docker Compose.

## 2 Work steps

### 2.1 Step 1: Project architecture

The selected scenario is **Online Order Processing System**. The implementation consists of three independent services and one broker:

- `order-service` (HTTP API + order database)
- `payment-service` (event consumer and publisher)
- `notification-service` (event consumer + notification database)
- `rabbitmq` (asynchronous broker)

Communication is implemented with topic routing keys and durable queues. This ensures event-based decoupling between services.

### 2.2 Step 2: Order Service

Order Service was implemented with FastAPI endpoints:

- `POST /orders` creates order and stores it in SQLite.
- `GET /orders/{id}` returns saved order.

After storing a new order, the service publishes the `order.created` event to the `events` exchange in RabbitMQ. The event includes order id, customer email, item name, amount, and timestamp.

### 2.3 Step 3: Payment Service

Payment Service subscribes to `order.created` messages through queue `payment.order.created`.

After receiving an order event, it simulates payment processing asynchronously. Result is generated as either:

- `payment.completed` (success), or
- `payment.failed` (failure with reason)

The service then publishes the result event back to RabbitMQ.

### 2.4 Step 4: Notification Service

Notification Service listens for both `payment.completed` and `payment.failed` events. For each received event, it composes a notification message and stores it in SQLite database.

This service simulates sending user notifications (for example, email or SMS) and logs processing output to container logs.

### 2.5 Step 5: Docker Compose integration and test

All components were integrated in `docker-compose.yml`:

- each service is built from its own Dockerfile,
- RabbitMQ runs as dedicated container,
- service ports are exposed for API access and monitoring,
- environment variables configure broker and database URLs.

System startup command:

```bash
docker compose up --build
```

Basic test scenario:

1. Send `POST /orders` request to Order Service.
2. Verify order is saved (`GET /orders/{id}`).
3. Observe logs of Payment and Notification services.
4. Confirm event chain executes asynchronously without direct service-to-service HTTP calls.

## 3 Conclusions

This homework demonstrates a working event-driven microservices system implemented with FastAPI and RabbitMQ. The architecture separates domain responsibilities and relies on asynchronous message exchange instead of direct inter-service calls.

During implementation, I practiced designing broker-based event flow, defining message schemas, and integrating services with Docker Compose. The result satisfies the core requirements of the assignment and provides a clean initial foundation for further improvements such as retries, dead-letter queues, observability, and automated tests.


# Attention 
This Markdown file is the original source of the document. The Word (.docx) version was generated from it using Pandoc utility. If any discrepancies occur, the content remains identical.