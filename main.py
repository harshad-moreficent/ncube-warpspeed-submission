import logging
import openai
from pathlib import Path
import pydantic
import telebot
from telebot.types import Message, BotCommand
import requests
from typing import Dict

from env_key import ENV_BOT_TOKEN, ENV_LOG_LEVEL, ENV_OPENAI_API_KEY, ENV_ELEVEN_LABS_API_KEY
from model import Character, ChatData

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


def run_bot(token: str, openai_api_key: str, eleven_labs_api_key: str,
            characters: Dict[str, Character]):
    bot = telebot.TeleBot(token)
    character_names = [
        x[0]
        for x in sorted([(k, v.sort_order) for k, v in characters.items()],
                        key=lambda x: x[1])
    ]
    log.info(f'Available characters: {character_names}')
    character_names_md = '\n'.join(
        [f'{idx + 1}. **{x}**' for idx, x in enumerate(character_names)])

    state: Dict[int, ChatData] = {}

    def handle_message(message: Message):
        chat_id = message.chat.id

        chat_data = state.get(chat_id)
        if chat_data is None:
            log.error(f'{chat_id} - chat data absent')
            bot.send_message(chat_id,
                             'Something has gone wrong. Please clear chat')
            return

        content_type = message.content_type
        message_id = message.message_id

        sent_message = None

        if content_type == 'text':
            log.info(f'{chat_id} - Got text input')
            reply = chat_data.get_text_response(message.text)

            sent_message = None
            if reply is None:
                reply = bot.send_message(chat_id,
                                         'Something went wrong. Please retry',
                                         reply_to_message_id=message_id)
            else:
                sent_message = bot.send_message(chat_id,
                                                reply,
                                                reply_to_message_id=message_id)

        elif content_type == 'voice':
            log.info(f'{chat_id} - got voice input')
            audio_data = get_audio(bot, chat_id, message.voice.file_id)
            if audio_data is None:
                log.error('{chat_id} - Failed to get audio file')
                sent_message = bot.send_message(
                    chat_id,
                    'Something went wrong. Please retry.',
                    reply_to_message_id=message_id)
            else:
                sent_message = bot.send_voice(chat_id,
                                              audio_data,
                                              reply_to_message_id=message.id)
        else:
            log.error(
                f'{chat_id} - Got unhandled content type: {content_type}')
            sent_message = bot.send_message(
                chat_id,
                "Your reply must be either text or a voice note",
                reply_to_message_id=message_id)

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
            chat_data = ChatData(chat_id=chat_id,
                                 character_name=character_name,
                                 character=characters[character_name])
            state.update({chat_id: chat_data})
            sent_message = bot.send_message(
                chat_id, f'Done. You are now chatting with {character_name}')
            bot.register_next_step_handler(sent_message, handle_message)

    @bot.message_handler(commands=["start"])
    def start_handler(message: Message):
        log.info('New Conversation')
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
        return

    openai_api_key = os.getenv(ENV_OPENAI_API_KEY)
    if openai_api_key is None:
        log.error(f'{ENV_OPENAI_API_KEY} not set')
        return
    openai.api_key = openai_api_key

    eleven_labs_api_key = os.getenv(ENV_ELEVEN_LABS_API_KEY)
    if eleven_labs_api_key is None:
        log.error(f'{ENV_ELEVEN_LABS_API_KEY} not set')
        return

    characters = None
    try:
        characters = pydantic.parse_file_as(Dict[str, Character],
                                            "characters.json")
    except pydantic.ValidationError as e:
        log.error(f'Failed to parse characters.json: {e.errors()}')
        return

    run_bot(bot_token, openai_api_key, eleven_labs_api_key, characters)


if __name__ == '__main__':
    main()

    print('ho gaya')
