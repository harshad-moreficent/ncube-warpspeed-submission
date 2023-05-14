from pydantic.dataclasses import dataclass


@dataclass
class Character:
    system_prompt: str
    chat_model: str
    voice: str
    tts_model: str
    sort_order: int
