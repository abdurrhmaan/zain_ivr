import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
import httpx
import asyncio
from typing import Dict, Any, Optional
import websockets
from websockets import connect
from ivr.config.settings import settings
from ivr.utils.logging import get_logger

logger = get_logger(__name__)

class ARIInterfaceABC(ABC):
    @abstractmethod
    async def answer_call(self, channel_id: str) -> None:
        pass

    @abstractmethod
    async def play_message(self, channel_id: str, message: str) -> None:
        pass

    @abstractmethod
    async def hangup_call(self, channel_id: str) -> None:
        pass

    @abstractmethod
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def websocket(self):
        pass

    @abstractmethod
    async def record_call(self, channel_id: str, name: str, max_duration: int) -> None:
        pass

    @abstractmethod
    async def start_dtmf_detection(self, channel_id: str):
        pass

    @abstractmethod
    async def stop_dtmf_detection(self, channel_id: str):
        pass

    @abstractmethod
    async def wait_for_dtmf(self, channel_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        pass



class ARIInterface(ARIInterfaceABC):
    def __init__(self):
        self.base_url = settings.ARI_BASE_URL
        self.auth = (settings.ARI_USER, settings.ARI_PASSWORD)
        self.max_retries = settings.ARI_MAX_RETRIES
        self.retry_delay = settings.ARI_RETRY_DELAY
        self.dtmf_events = {}

    async def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await getattr(client, method)(url, auth=self.auth, **kwargs)
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e}")
                raise
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed, retrying in {self.retry_delay} seconds.")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise

    async def start_dtmf_detection(self, channel_id: str):
        url = f"{self.base_url}/ari/channels/{channel_id}/detect/dtmf"
        await self._make_request('post', url)
        logger.info(f"Started DTMF detection on channel: {channel_id}")

    async def stop_dtmf_detection(self, channel_id: str):
        url = f"{self.base_url}/ari/channels/{channel_id}/detect/dtmf"
        await self._make_request('delete', url)
        logger.info(f"Stopped DTMF detection on channel: {channel_id}")

    async def wait_for_dtmf(self, channel_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        future = asyncio.get_event_loop().create_future()
        self.dtmf_events[channel_id] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            logger.info(f"Timeout waiting for DTMF on channel {channel_id}")
            return None
        finally:
            self.dtmf_events.pop(channel_id, None)

    async def answer_call(self, channel_id: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}/answer"
        await self._make_request('post', url)
        logger.info(f"Answered call for channel: {channel_id}")

    async def play_message(self, channel_id: str, message: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}/play"
        await self._make_request('post', url, json={"media": message})
        logger.info(f"Playing message {message} on channel: {channel_id}")

    async def record_call(self, channel_id: str, name: str, max_duration: int) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}/record"
        params = {
            "name": name,
            "format": "wav",
            "maxDurationSeconds": max_duration
        }
        await self._make_request('post', url, params=params)
        logger.info(f"Started recording {name} on channel: {channel_id}")

    async def hangup_call(self, channel_id: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}"
        await self._make_request('delete', url)
        logger.info(f"Hung up call on channel: {channel_id}")

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/ari/channels/{channel_id}"
        response = await self._make_request('get', url)
        return response.json()

    async def websocket(self):
        uri = f"ws://{self.base_url.split('://')[-1]}/ari/events?app=simple_ivr&subscribeAll=true"
        return connect(uri)

    async def events_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        uri = f"ws://{self.base_url.split('://')[-1]}/ari/events?app=simple_ivr&subscribeAll=true"
        while True:
            try:
                async with connect(uri, extra_headers={
                    'Authorization': f'Basic {self.auth[0]}:{self.auth[1]}'
                }) as websocket:
                    async for message in websocket:
                        event = json.loads(message)
                        await self._handle_event(event)
                        yield event
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(self.retry_delay)
