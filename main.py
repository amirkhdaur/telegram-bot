import telebot
from telebot import types
import config
import sqlite3


bot = telebot.TeleBot(config.TELEGRAM_TOKEN, parse_mode='HTML')

bot_info = bot.get_me()
bot_id = bot_info.id

document_types = [
    'Счёт к оплате',
    'АВР/накладная',
    'Доверенность',
    'Акт сверки',
    'Прочие',
]


def get_info(user_id):
    connect = sqlite3.connect('users.db')
    cursor = connect.cursor()
    cursor.execute(f'SELECT * FROM users WHERE user_id = ?', [user_id])
    data = cursor.fetchone()
    connect.close()
    if data:
        return data[0]
    else:
        return None


@bot.message_handler(commands=['getchatid'])
def get_chat_id(message):
    bot.reply_to(message, message.chat.id)


@bot.message_handler(commands=['start'], chat_types=['private'])
def start(message):
    text = ('Перед тем как начать, отправьте ваше имя и компанию через запятую.\n'
            'Пример: Иван, ТОО Mega kz')
    bot.send_message(message.chat.id, text=text)


@bot.message_handler(commands=['resetinfo'], chat_types=['private'])
def reset_info(message):
    connect = sqlite3.connect('users.db')
    cursor = connect.cursor()
    cursor.execute(f'DELETE FROM users WHERE user_id = ?', [message.from_user.id])
    connect.commit()
    connect.close()
    bot.send_message(message.chat.id, text='Сброшено')
    start(message)


@bot.message_handler(chat_types=['private'], content_types=['text', 'document', 'photo'],
                     func=lambda message: not get_info(message.from_user.id))
def handle_info(message):
    if message.text and len(message.text.split(',')) == 2:
        connect = sqlite3.connect('users.db')
        cursor = connect.cursor()
        cursor.execute(f'INSERT INTO users VALUES (?, ?)', [message.text, message.from_user.id])
        connect.commit()
        connect.close()
        text = ('Готово! Теперь вы можете отправлять сообщения.\n'
                'Если вам потребуется поменять эти данные, используйте команду /resetinfo для сброса.')
        bot.send_message(message.chat.id, text=text)
    else:
        text = ('Пожалуйста, отправьте ваше имя и компанию через запятую.\n'
                'Пример: Иван, ТОО Mega kz')
        bot.send_message(message.chat.id, text=text)


def handle_reply_check(message):
    return (str(message.chat.id) == config.TELEGRAM_MAIN_CHAT_ID and
            message.reply_to_message and message.reply_to_message.from_user.id == bot_id)


@bot.message_handler(content_types=['text', 'document', 'photo'], func=handle_reply_check)
def handle_reply(message):
    if message.reply_to_message.text:
        message_text = message.reply_to_message.text
    else:
        message_text = message.reply_to_message.caption

    ids = message_text.split('\n')[0][4:].split('_')
    chat_id = ids[0]
    message_id = ids[1]
    if message.document:
        bot.send_document(chat_id, document=message.document.file_id, caption=message.caption,
                          reply_to_message_id=message_id)
    elif message.photo:
        bot.send_photo(chat_id, photo=message.photo[0].file_id, caption=message.caption, reply_to_message_id=message_id)
    else:
        bot.send_message(chat_id, text=message.text, reply_to_message_id=message_id)


@bot.message_handler(content_types=['text', 'document', 'photo'], chat_types=['private'],
                     func=lambda message: str(message.chat.id) != config.TELEGRAM_MAIN_CHAT_ID)
def handle_document(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton(text, callback_data=str(index))
        for index, text in enumerate(document_types)
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id,
                     text='Выберите тип заявки:',
                     reply_to_message_id=message.id,
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    bot.edit_message_text('Принято в работу', call.message.chat.id, call.message.id)
    document_type = int(call.data)

    message = call.message.reply_to_message
    text = f'ID: {call.message.chat.id}_{message.id}\n' + \
           f'Клиент: {get_info(call.from_user.id)}\n' + \
           f'Тип заявки: <b>{document_types[document_type]}</b>'

    message_text = None
    if message.text:
        message_text = message.text
    elif message.caption:
        message_text = message.caption

    if message_text:
        text += f'\n\n{message_text}'

    if message.document:
        bot.send_document(config.TELEGRAM_MAIN_CHAT_ID, document=message.document.file_id, caption=text)
    elif message.photo:
        bot.send_photo(config.TELEGRAM_MAIN_CHAT_ID, photo=message.photo[0].file_id, caption=text)
    else:
        bot.send_message(config.TELEGRAM_MAIN_CHAT_ID, text=text)


bot.polling()
