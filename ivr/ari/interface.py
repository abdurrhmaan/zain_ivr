from abc import ABC, abstractmethod
import httpx
import asyncio
from typing import Dict, Any
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

class ARIInterface(ARIInterfaceABC):
    def __init__(self):
        self.base_url = settings.ARI_BASE_URL
        self.auth = (settings.ARI_USER, settings.ARI_PASSWORD)
        self.max_retries = settings.ARI_MAX_RETRIES
        self.retry_delay = settings.ARI_RETRY_DELAY

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
                    logger.warning(f"Request failed, retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise

    async def answer_call(self, channel_id: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}/answer"
        await self._make_request('post', url)
        logger.info(f"Answered call for channel: {channel_id}")

    async def play_message(self, channel_id: str, message: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}/play"
        await self._make_request('post', url, json={"media": message})
        logger.info(f"Playing message {message} on channel: {channel_id}")

    async def hangup_call(self, channel_id: str) -> None:
        url = f"{self.base_url}/ari/channels/{channel_id}"
        await self._make_request('delete', url)
        logger.info(f"Hung up call on channel: {channel_id}")

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/ari/channels/{channel_id}"
        response = await self._make_request('get', url)
        return response.json()

    async def websocket(self):
        uri = f"{self.base_url}/ari/events?app=simple_ivr"
        return httpx.AsyncClient().websocket(uri, auth=self.auth)
