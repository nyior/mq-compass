# Source Harvester

This FastAPI service models the source monitoring layer for the assistant.

It is intentionally simple:

- accepts source definitions
- performs a mock harvest
- returns a LavinMQ-ready job payload
