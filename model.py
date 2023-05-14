from pydantic.dataclasses import dataclass


@dataclass
class Character:
    name: str
    system_prompt: str
    chat_model: str
    voice: str
    tts_model: str
