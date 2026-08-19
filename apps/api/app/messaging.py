from __future__ import annotations
import json
import pika
from .config import settings

EXCHANGE = "flowpilot"
RUN_QUEUE = "flowpilot.run"
DLQ = "flowpilot.dlq"

def _channel():
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    ch = connection.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=RUN_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
    ch.queue_declare(queue=DLQ, durable=True, arguments={"x-queue-type": "quorum"})
    ch.queue_bind(queue=RUN_QUEUE, exchange=EXCHANGE, routing_key="run")
    ch.queue_bind(queue=DLQ, exchange=EXCHANGE, routing_key="dlq")
    return connection, ch

def publish_run(run_id: str, action: str = "execute") -> None:
    conn, ch = _channel()
    ch.basic_publish(exchange=EXCHANGE, routing_key="run", body=json.dumps({"run_id": run_id, "action": action}).encode(), properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"))
    conn.close()

def publish_dlq(run_id: str, reason: str) -> None:
    conn, ch = _channel()
    ch.basic_publish(exchange=EXCHANGE, routing_key="dlq", body=json.dumps({"run_id": run_id, "reason": reason}).encode(), properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"))
    conn.close()
