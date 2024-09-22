from abc import ABC, abstractmethod
from typing import Dict, Any
from ivr.ari.interface import ARIInterfaceABC
from ivr.utils.logging import get_logger

logger = get_logger(__name__)

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
        await self.ari.play_message(channel_id, "sound:welcome_message")
        return MainMenuState(self.ari)

class MainMenuState(CallState):
    async def handle(self, event: Dict[str, Any]) -> 'CallState':
        channel_id = event['channel']['id']
        await self.ari.play_message(channel_id, "sound:main_menu_options")
        # Here you would typically wait for DTMF input and transition to the appropriate state
        # For simplicity, we'll just return to the welcome state
        return WelcomeState(self.ari)

class CallHandler:
    def __init__(self, ari: ARIInterfaceABC):
        self.ari = ari
        self.current_state: CallState = WelcomeState(ari)

    async def handle_event(self, event: Dict[str, Any]):
        try:
            event_type = event['type']
            if event_type == 'StasisStart':
                self.current_state = await self.current_state.handle(event)
            elif event_type == 'StasisEnd':
                logger.info(f"Call ended for channel {event['channel']['id']}")
            # Add more event type handlers as needed
        except Exception as e:
            logger.error(f"Error handling event: {str(e)}")