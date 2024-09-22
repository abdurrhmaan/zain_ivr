from abc import ABC, abstractmethod
from typing import Dict, Any
from ivr.ari.interface import ARIInterfaceABC
from ivr.utils.logging import get_logger
import asyncio

logger = get_logger(__name__)

WELCOME_MESSAGE_AR = 'sound:custom/alsun/ar/1_welcome'
PRESS_1_ENGLISH = 'sound:custom/alsun/en/37_english_language'
WELCOME_MESSAGE_EN = 'sound:custom/alsun/en/1_welcome'

class CallState(ABC):
    def __init__(self, ari: ARIInterfaceABC):
        self.ari = ari

    @abstractmethod
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        pass

class WelcomeState(CallState):
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        channel_id = event['channel']['id']
        await self.ari.answer_call(channel_id)
        await self.ari.play_message(channel_id, WELCOME_MESSAGE_AR)
        await self.ari.play_message(channel_id, PRESS_1_ENGLISH)
        return LanguageSelectionState(self.ari)

class LanguageSelectionState(CallState):
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        channel_id = event['channel']['id']

        await self.ari.start_dtmf_detection(channel_id)

        try:
            dtmf_event = await self.ari.wait_for_dtmf(channel_id, timeout=2.0)
            if dtmf_event and dtmf_event['digit'] == '1':
                await self.ari.play_message(channel_id, WELCOME_MESSAGE_EN)
            else:
                logger.info(f"Continuing in Arabic for channel {channel_id}")
        finally:
            await self.ari.stop_dtmf_detection(channel_id)

        return RecordState(self.ari)

class RecordState(CallState):
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        channel_id = event['channel']['id']
        while True:
            recording_name = f"recording_{channel_id}_{int(asyncio.get_event_loop().time())}"
            await self.ari.record_call(channel_id, recording_name, max_duration=10)

            await self.ari.play_message(channel_id, f"sound:{recording_name}.wav")

            channel_info = await self.ari.get_channel_info(channel_id)
            if channel_info['state'] == 'Hangup':
                return HangupState(self.ari)  # Transition to HangupState

        return HangupState(self.ari)  # Fallback in case the loop exits unexpectedly.

class HangupState(CallState):
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        channel_id = event['channel']['id']
        logger.info(f"Call has been hung up for channel {channel_id}")
        return None  # End of the state machine.

class CallHandler:
    def __init__(self, ari: ARIInterfaceABC):
        self.ari = ari
        self.current_state: CallState = WelcomeState(ari)

    async def handle_event(self, event: Dict[str, Any]):
        try:
            event_type = event['type']
            if event_type == 'StasisStart':
                while self.current_state:
                    self.current_state = await self.current_state.handle(event)
            elif event_type == 'StasisEnd':
                logger.info(f"Call ended for channel {event['channel']['id']}")
        except Exception as e:
            logger.error(f"Error handling event: {str(e)}")
