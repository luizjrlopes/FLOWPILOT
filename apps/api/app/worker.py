from __future__ import annotations
import json
import pika
from .config import settings
from .db import SessionLocal, init_db
from .engine import execute
from .messaging import EXCHANGE, RUN_QUEUE
from .seed import seed

def main():
    init_db()
    with SessionLocal() as db: seed(db)
    connection=pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url));ch=connection.channel()
    ch.exchange_declare(exchange=EXCHANGE,exchange_type="direct",durable=True)
    ch.queue_declare(queue=RUN_QUEUE,durable=True,arguments={"x-queue-type":"quorum"});ch.queue_bind(queue=RUN_QUEUE,exchange=EXCHANGE,routing_key="run");ch.basic_qos(prefetch_count=1)
    def callback(channel,method,properties,body):
        payload=json.loads(body);run_id=payload["run_id"]
        try:
            with SessionLocal() as db: execute(db,run_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            channel.basic_nack(delivery_tag=method.delivery_tag,requeue=False)
    ch.basic_consume(queue=RUN_QUEUE,on_message_callback=callback);print("FlowPilot worker ready",flush=True);ch.start_consuming()
if __name__=="__main__": main()
