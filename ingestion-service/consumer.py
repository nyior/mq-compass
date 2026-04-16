import json
import logging
from typing import Callable

import pika


logger = logging.getLogger(__name__)


class QueueConsumer:
    def __init__(self, amqp_url: str, queue_name: str) -> None:
        self.amqp_url = amqp_url
        self.queue_name = queue_name

    def consume_forever(self, handler: Callable[[dict], None]) -> None:
        params = pika.URLParameters(self.amqp_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)

        def _on_message(ch, method, _properties, body: bytes) -> None:
            try:
                payload = json.loads(body.decode("utf-8"))
                handler(payload)
            except Exception:
                logger.exception("Message processing failed. Leaving message unacked for retry.")
                return

            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=self.queue_name, on_message_callback=_on_message, auto_ack=False)
        logger.info("Consuming queue '%s'", self.queue_name)
        channel.start_consuming()
