from dataclasses import dataclass
import elevenlabs
from pydantic.dataclasses import dataclass as pydantic_dataclass
import logging
from pathlib import Path
import openai
from tenacity import retry, stop_after_delay, stop_after_attempt
from typing import List, Optional

log = logging.getLogger(Path(__file__).stem)


@pydantic_dataclass(frozen=True)
class Character:
    system_prompt: str
    chat_model: str
    voice: str
    tts_model: str
    sort_order: int


@dataclass
class ChatMessage:
    role: str
    context: str


class ChatData:
    __chat_id: int
    __character_name: str
    __chat_model: str
    __voice: str
    __tts_model: str
    __chat_history: List[ChatMessage]

    def __init__(self, chat_id: int, character_name: str,
                 character: Character):
        self.__chat_id = chat_id
        self.__character_name = character_name
        self.__chat_model = character.chat_model
        self.__voice = character.voice
        self.__tts_model = character.tts_model
        self.__chat_history = [{
            "role": "system",
            "content": character.system_prompt
        }]

    @property
    def character_name(self) -> str:
        return self.__character_name
    
    @retry(stop=(stop_after_delay(10) | stop_after_attempt(20)))
    def tts(self, text: str):
        audio = elevenlabs.generate(
		  text=text,
		  voice=self.__voice,
		  model=self.__tts_model
		)
        return audio

    @retry(stop=(stop_after_delay(10) | stop_after_attempt(20)))
    def get_text_response(self, text: str):
        try:
            self.__chat_history.append({"role": "user", "content": text})
            response = openai.ChatCompletion.create(
                model=self.__chat_model, messages=self.__chat_history
            )['choices'][0]['message']['content']
            self.__chat_history.append({
                "role": "assistant",
                "content": response
            })
            return self.tts(response)
            # return response
        except (openai.error.APIError, openai.error.AuthenticationError,
                open.error.RateLimitError,
                openai.error.ServiceUnavailableError) as e:
            self.__chat_history.pop()
            log.error(f'{self.__chat_id} - openai error: {e}')
