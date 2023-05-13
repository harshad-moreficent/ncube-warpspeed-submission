import telebot
import requests

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

def run_bot(token: str):
    bot = telebot.TeleBot(token)

    def fetch_horoscope(message, sign):
        day = message.text
        horoscope = get_daily_horoscope(sign, day)
        print(horoscope)
        data = horoscope["data"]
        horoscope_message = f'*Horoscope:* {data["horoscope_data"]}\\n*Sign:* {sign}\\n*Day:* {data["date"]}'
        bot.send_message(message.chat.id, "Here's your horoscope!")
        bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")


    def day_handler(message):
        sign = message.text
        text = "What day do you want to know?\nChoose one: *Today*, *Tomorrow*, *Yesterday*"
        sent_message = bot.send_message(message.chat.id, text, parse_mode="Markdown")
        bot.register_next_step_handler(sent_message, fetch_horoscope, sign.capitalize())

    @bot.message_handler(commands=["horoscope"])
    def sign_handler(message):
        text = "What is your zodiac sign?\nChoose one: *Aries*, *Taurus*"
        sent_message = bot.send_message(message.chat.id, text, parse_mode="Markdown")
        bot.register_next_step_handler(sent_message, day_handler)

    bot.infinity_polling()

if __name__ == '__main__':
    import os

    bot_token = os.getenv('BOT_TOKEN')
    if bot_token is None:
        raise Exception("BOT_TOKEN not set")
    
    run_bot(bot_token)

    print('ho gaya')