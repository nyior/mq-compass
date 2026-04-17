import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from main import IngestionWorker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

worker_status = {
    "running": False,
    "last_error": None,
    "started_at": None,
}


def run_worker_forever() -> None:
    while True:
        worker_status["running"] = False
        worker_status["started_at"] = time.time()
        try:
            logger.info("Starting ingestion worker")
            worker_status["last_error"] = None
            worker_status["running"] = True
            IngestionWorker().run()
        except Exception as exc:
            worker_status["running"] = False
            worker_status["last_error"] = str(exc)
            logger.exception("Ingestion worker stopped unexpectedly; restarting soon")
            time.sleep(5)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in ("/", "/health"):
            self.send_error(404)
            return

        payload = {
            "status": "ok",
            "service": "ingestion-service",
            "worker_status": "running" if worker_status["running"] else "starting",
            "worker": worker_status,
        }
        body = json.dumps(payload).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        logger.info("HTTP %s", format % args)


def main() -> None:
    port = int(os.getenv("PORT", "8102"))
    worker_thread = threading.Thread(target=run_worker_forever, daemon=True)
    worker_thread.start()

    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Ingestion service health server listening on port %s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
