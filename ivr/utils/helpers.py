import asyncio
import logging

async def wait_for_event(condition: asyncio.Condition, timeout: float):
    try:
        await asyncio.wait_for(condition.wait(), timeout)
    except asyncio.TimeoutError:
        logging.error("Timeout waiting for event")

