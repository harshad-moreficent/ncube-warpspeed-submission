import json
import logging
from pathlib import Path
import pydantic
import telebot
from telebot.types import Message, BotCommand
import requests
from typing import Dict
import urllib

from env_key import ENV_BOT_TOKEN, ENV_LOG_LEVEL
from model import Character

log = logging.getLogger(Path(__file__).stem)

BOT_NAME = 'CelebVox'


def get_audio(bot: telebot.TeleBot, chat_id: str, file_id: str):
    file_info = bot.get_file(file_id)
    if file_info is None:
        log.error(f'{chat_id}: Failed to get audio file info')
        return None
    audio_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
    resp = requests.get(audio_url, allow_redirects=True)
    if resp is None:
        log.error(f'{chat_id} - Failed to get resp')
    
    return resp.content


def run_bot(token: str, characters: Dict[str, Character]):
    bot = telebot.TeleBot(token)
    character_names = [
        x[0]
        for x in sorted([(k, v.sort_order) for k, v in characters.items()],
                        key=lambda x: x[1])
    ]
    log.info(f'Available characters: {character_names}')
    character_names_md = '\n'.join(
        [f'{idx + 1}. **{x}**' for idx, x in enumerate(character_names)])

    def handle_message(message: Message):
        chat_id = message.chat.id
        content_type = message.content_type
        print(message.content_type)
        sent_message = None
        if content_type == 'text':
            log.debug(f'{chat_id} - Got text input')
            sent_message = bot.send_message(chat_id, message.text)
        elif content_type == 'voice':
            log.debug(f'{chat_id} - got voice input')
            audio_data = get_audio(bot, chat_id, message.voice.file_id)
            if audio_data is None:
                log.error('{chat_id} - Failed to get audio file')
                sent_message = bot.send_message(
                    chat_id, 'Something went wrong. Please retry.')
            else:
                sent_message = bot.send_audio(chat_id, audio_data)
        else:
            log.error(
                f'{chat_id} - Got unhandled content type: {content_type}')
            sent_message = bot.send_message(
                chat_id, "Your reply must be either text or a voice note")
        bot.register_next_step_handler(sent_message, handle_message)

    def chat_init_handler(message: Message):
        character_name = message.text
        if character_name not in characters.keys():
            log.warn(f'Got unhandled character: {character_name}')
            sent_message = bot.reply_to(
                message,
                f'Sorry, that character is not available. Please choose one of:\n\n{character_names_md}',
                parse_mode="Markdown")
            bot.register_next_step_handler(sent_message, chat_init_handler)
        else:
            chat_id = message.chat.id
            log.info(
                f'Starting a conversation with {character_name}. id: {chat_id}'
            )
            bot.send_message(chat_id, "Setting things up...")
            # set up chat llm and other APIs
            sent_message = bot.send_message(
                chat_id, f'Done. You are now chatting with {character_name}')
            bot.register_next_step_handler(sent_message, handle_message)

    @bot.message_handler(commands=["start"])
    def start_handler(message: Message):
        log.debug('New Conversation')
        sent_message = bot.reply_to(
            message,
            f'Hi, welcome to {BOT_NAME}. Please choose the celebrity you wish to chat with:\n\n{character_names_md}',
            parse_mode="Markdown")
        bot.register_next_step_handler(sent_message, chat_init_handler)

    log.info('Beginning bot polling')
    bot.infinity_polling()


def main():
    import os

    log_level = os.getenv(ENV_LOG_LEVEL)
    if log_level:
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=
            '[%(asctime)s %(levelname)s %(module)s - %(funcName)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    log.info('Beginning BotHandlers')

    bot_token = os.getenv(ENV_BOT_TOKEN)
    if bot_token is None:
        log.error(f'{ENV_BOT_TOKEN} not set')

    characters = None
    try:
        characters = pydantic.parse_file_as(Dict[str, Character],
                                            "characters.json")
    except pydantic.ValidationError as e:
        log.error(f'Failed to parse characters.json: {e.errors()}')
        return

    run_bot(bot_token, characters)


if __name__ == '__main__':
    main()

    print('ho gaya')
