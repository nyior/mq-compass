from __future__ import annotations

import json
from typing import Any

import pika


class QueuePublisher:
    def __init__(self, amqp_url: str, queue_name: str = "ingestion_jobs") -> None:
        self.amqp_url = amqp_url
        self.queue_name = queue_name

    def publish(self, payload: dict[str, Any]) -> None:
        params = pika.URLParameters(self.amqp_url)
        params.heartbeat = 30
        params.blocked_connection_timeout = 30

        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.confirm_delivery()
            message = json.dumps(payload)
            channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
                mandatory=True,
            )
        finally:
            connection.close()
