import json
import logging
from pathlib import Path
import pydantic
import telebot
import requests
from typing import List

from env_key import ENV_BOT_TOKEN, ENV_LOG_LEVEL
from model import Character

log = logging.getLogger(Path(__file__).stem)


def get_daily_horoscope(sign: str, day: str) -> dict:
    """Get daily horoscope for a zodiac sign.
    Keyword arguments:
    sign:str - Zodiac sign
    day:str - Date in format (YYYY-MM-DD) OR TODAY OR TOMORROW OR YESTERDAY
    Return:dict - JSON data
    """
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params)

    return response.json()


def run_bot(token: str, characters: List[Character]):
    bot = telebot.TeleBot(token)

    def fetch_horoscope(message, sign):
        day = message.text
        horoscope = get_daily_horoscope(sign, day)
        print(horoscope)
        data = horoscope["data"]
        horoscope_message = f'*Horoscope:* {data["horoscope_data"]}\\n*Sign:* {sign}\\n*Day:* {data["date"]}'
        bot.send_message(message.chat.id, "Here's your horoscope!")
        bot.send_message(message.chat.id,
                         horoscope_message,
                         parse_mode="Markdown")

    def day_handler(message):
        sign = message.text
        text = "What day do you want to know?\nChoose one: *Today*, *Tomorrow*, *Yesterday*"
        sent_message = bot.send_message(message.chat.id,
                                        text,
                                        parse_mode="Markdown")
        bot.register_next_step_handler(sent_message, fetch_horoscope,
                                       sign.capitalize())

    @bot.message_handler(commands=["horoscope"])
    def sign_handler(message):
        text = "What is your zodiac sign?\nChoose one: *Aries*, *Taurus*"
        sent_message = bot.send_message(message.chat.id,
                                        text,
                                        parse_mode="Markdown")
        bot.register_next_step_handler(sent_message, day_handler)

    @bot.message_handler(commands=["start"])
    def start_handler(message):
        bot.reply_to(
            message,
            "Hi, welcome to CelebVox. Please choose the celebrity you wish to chat with:"
        )

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
        characters = pydantic.parse_file_as(List[Character], "characters.json")
    except pydantic.ValidationError as e:
        log.error(f'Failed to parse characters.json: {e.errors()}')
        return
    
    character_names = {character.name for character in characters}
    if len(character_names) != len(characters):
        log.error('Duplicate character names')
        return

    run_bot(bot_token, characters)


if __name__ == '__main__':
    main()

    print('ho gaya')
