import telebot
from telebot import types
import requests
import os

bot = telebot.TeleBot(os.environ['Telegram_Token'])

a = dict()  # Переменная a отвечает за выполнение блока,
# связанного с конвертацией валют непосредственно, для каждого она своя

to_or_from = dict()  # Если данная переменная = 1, то мы переводим из рублей в валюту,
# иначе - в рубли из валюты, для каждого пользователя он своя

currency = dict()  # Переменная currency отвечает за выбранную валюту,
# для каждого пользователя она своя, так же как и две предыдущих


# Данный блок не убран, т.к. он служит для получения id стикера, что бывает очень полезно
# @bot.message_handler(content_types=['sticker'])
# def welcome(message):
#     print(message.sticker.file_id)


@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(1)
    item1 = types.KeyboardButton("$")
    item2 = types.KeyboardButton("€")
    item3 = types.KeyboardButton("другая валюта")
    item4 = types.KeyboardButton('а откуда данные?')
    markup.add(item1, item2, item3, item4)

    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAICqF_vkbY4JoMT7LB7u8ybckSALiYPAAJIBAACztjoC8AMSL-Qm9uMHgQ')
    bot.send_message(message.chat.id, 'Я - бот, который умеет конвертировать рубли в валюту, или, наоборот')
    bot.send_message(message.chat.id, 'Что из предложенного интересует?'
                                      ' Просто нажми на кнопку внизу, а дальше разберёмся', reply_markup=markup)


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
        currency[message.chat.id] = 'EUR'
        inline_markup(message)

    elif message.text == '$':
        currency[message.chat.id] = 'USD'
        inline_markup(message)

    elif message.text == 'другая валюта':
        a[message.chat.id] = 0
        bot.send_message(message.chat.id, 'Введи валюту в формате ISO 4217')

    elif message.text == 'а откуда данные?':
        bot.send_message(message.chat.id, 'Все курсы я беру с сайта ЦБРФ, '
                                          'вот, собственно, и он https://www.cbr.ru/currency_base/daily/')
        bot.send_message(message.chat.id, 'И да, курсы в обменниках могут отличаться. Хвала нашему законодательству)')

    elif a[message.chat.id] == 1:
        try:
            currency1 = ('RUB' if to_or_from[message.chat.id] == 1 else str(currency[message.chat.id]))
            currency2 = (str(currency[message.chat.id]) if to_or_from[message.chat.id] == 1 else 'RUB')
            value = "%.3f" % (float(message.text) * requests.get('https://www.cbr-xml-daily.ru/latest.js')
                              .json()['rates'][currency[message.chat.id]] if to_or_from[message.chat.id] == 1 else
                              float(message.text) / requests.get('https://www.cbr-xml-daily.ru/latest.js')
                              .json()['rates'][currency[message.chat.id]])
            bot.send_message(message.chat.id, f'{message.text} {currency1} - это {value} {currency2}')

            del a[message.chat.id]
            del currency[message.chat.id]
            del to_or_from[message.chat.id]
        except ValueError:
            a[message.chat.id] = 1

    else:
        try:
            test = requests.get('https://www.cbr-xml-daily.ru/latest.js').json()['rates'][message.text]
            currency[message.chat.id] = message.text
            inline_markup(message)
        except KeyError:
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAICrF_vkeKrTq6OFXkCWBZx1Taz3wNxAAIcAwACztjoC3bCGmnfsBbDHgQ')
            bot.send_message(message.chat.id, 'Выбери, пожалуйста, один из вариантов со встроенной клавиатуры'
                                              ' или введи один из поддерживаемых кодов валют')
            bot.send_message(message.chat.id, 'А вот, кстати, и они:')
            bot.send_photo(message.chat.id, photo=open('currencies.png', 'rb'))
            bot.send_message(message.chat.id, 'Только, пожалуйста, введи курс именно большими буквами')


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
        line = '1 ' + str(currency[call.message.chat.id]) + ' сейчас стоит ' + str("%.3f" % (1 / requests.get(
            'https://www.cbr-xml-daily.ru/latest.js').json()['rates'][currency[call.message.chat.id]])) + ' RUB'
        bot.send_message(call.message.chat.id, text=line)

    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    if call.data == 'to_currency':
        to_or_from[call.message.chat.id] = 1
        bot.send_message(call.message.chat.id, 'Введи сумму, которую хочешь преобразовать')
        a[call.message.chat.id] = 1
    elif call.data == 'from_currency':
        to_or_from[call.message.chat.id] = 0
        bot.send_message(call.message.chat.id, 'Введи сумму которую хочешь преобразовать')
        a[call.message.chat.id] = 1


bot.polling(none_stop=True, interval=0)
