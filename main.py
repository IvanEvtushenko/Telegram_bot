import telebot
from telebot import types
import requests
import Token


a: bool
a = False  # Переменная a отвечает за выполнение блока с обработкой самостоятельно введённого кода валюты
to_or_from: bool  # Если данная переменная = 1, ты мы переводим из рублей в валюту, иначе - в рубли из валюты
currency: str

bot = telebot.TeleBot(Token.Telegram_TOKEN)


# @bot.message_handler(content_types=['sticker'])
# def welcome(message):
#     print(message.sticker.file_id)


@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(1)
    item1 = types.KeyboardButton("$")
    item2 = types.KeyboardButton("€")
    item3 = types.KeyboardButton("другая валюта")
    markup.add(item1, item2, item3)

    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAICqF_vkbY4JoMT7LB7u8ybckSALiYPAAJIBAACztjoC8AMSL-Qm9uMHgQ')
    bot.send_message(message.chat.id, 'Я - бот, который умеет конвертировать рубли в валюту, или, наоборот')
    bot.send_message(message.chat.id, 'Что из предложенного интересует? Просто нажми на кнопку внизу, а дальше разберёмся)', reply_markup=markup)


def inline_markup(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    key1 = types.InlineKeyboardButton("Сконвертируй", callback_data='conversion')
    key2 = types.InlineKeyboardButton("Выдай курс", callback_data='rate')
    keyboard.add(key1, key2)
    bot.send_message(message.chat.id, 'хм, а что из этого нужно сделать?', reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def voting_processing(message):
    global currency
    global to_or_from
    global a

    if message.text == '€':
        currency = 'EUR'
        inline_markup(message)

    elif message.text == '$':
        currency = 'USD'
        inline_markup(message)

    elif message.text == 'другая валюта':
        bot.send_message(message.chat.id, 'Введи валюту в формате ISO 4217')

    elif a:
        try:
            currency1 = ('RUB' if to_or_from == 1 else currency)
            currency2 = (currency if to_or_from == 1 else 'RUB')
            value = "%.3f" % (float(message.text) * requests.get('https://www.cbr-xml-daily.ru/latest.js').json()['rates'][currency] if to_or_from == 1 else
                     float(message.text) / requests.get('https://www.cbr-xml-daily.ru/latest.js').json()['rates'][currency])
            bot.send_message(message.chat.id, f'{message.text} {currency1} - это {value} {currency2}')
            a = 0
        except ValueError:
            a = 1

    else:
        try:
            requests.get('https://www.cbr-xml-daily.ru/latest.js').json()['rates'][message.text]
            currency = message.text
            inline_markup(message)
        except KeyError:
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAICrF_vkeKrTq6OFXkCWBZx1Taz3wNxAAIcAwACztjoC3bCGmnfsBbDHgQ')
            bot.send_message(message.chat.id, 'Выбери, пожалуйста, один из вариантов со встроенной клавиатуры или введи один из поддерживаемых кодов валют')
            bot.send_message(message.chat.id, 'А вот, кстати, и они:')
            bot.send_photo(message.chat.id, photo=open('currencies.png', 'rb'))


def inline_markup_range_2(call):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    key1 = types.InlineKeyboardButton('из рублей в валюту', callback_data='to_currency')
    key2 = types.InlineKeyboardButton('из валюты в рубли', callback_data='from_currency')
    keyboard.add(key1, key2)
    bot.send_message(chat_id=call.message.chat.id, text='Выбери один из вариантов', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global currency
    global to_or_from
    global a
    if call.data == 'conversion':
        inline_markup_range_2(call)
    elif call.data == 'rate':
        line = '1 ' + str(currency) + ' сейчас стоит ' + str("%.3f" % (1 / requests.get('https://www.cbr-xml-daily.ru/latest.js').json()['rates'][currency])) + ' RUB'
        bot.send_message(call.message.chat.id, text=line)

    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    if call.data == 'to_currency':
        to_or_from = True
        bot.send_message(call.message.chat.id, 'Введи сумму, которую хочешь преобразовать')
        a = True
    elif call.data == 'from_currency':
        to_or_from = False
        bot.send_message(call.message.chat.id, 'Введи сумму которую хочешь преобразовать')
        a = True


bot.polling(none_stop=True, interval=0)