import asyncio
import signal
from ivr.ari.interface import ARIInterface
from ivr.call_flow.handler import CallHandler
from ivr.utils.logging import get_logger
from ivr.config.settings import settings

logger = get_logger(__name__)

shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    shutdown_event.set()

async def main():
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    ari = ARIInterface()
    call_handler = CallHandler(ari)

    while not shutdown_event.is_set():
        try:
            async with ari.websocket() as websocket:
                logger.info("Connected to ARI WebSocket.")
                async for message in websocket:
                    if shutdown_event.is_set():
                        break
                    await call_handler.handle_event(message)
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            if not shutdown_event.is_set():
                await asyncio.sleep(5)  # Wait before reconnecting

    logger.info("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())