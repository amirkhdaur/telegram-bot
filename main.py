import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

bot_info = bot.get_me()
bot_id = bot_info.id

document_types = [
    'счёт на оплату от продавца',
    'счёт на оплату покупателю',
    'счет к оплате',
    'акт выполненных работ/ накладная на товар от продавца',
    'акт выполненных работ/ накладная на товар для покупателя',
    'доверенность на получение товара',
    'акт сверки',
    'прочее'
]

users = {}


@bot.message_handler(commands=['getchatid'])
def get_chat_id(message):
    bot.reply_to(message, message.chat.id)


def handle_reply_check(message):
    return (str(message.chat.id) == config.TELEGRAM_MAIN_CHAT_ID and
            message.reply_to_message and message.reply_to_message.from_user.id == bot_id)


@bot.message_handler(content_types=['text', 'document', 'photo'], func=handle_reply_check)
def handle_reply(message):
    text = message.text
    ids = message.reply_to_message.text.split('\n')[0][4:].split('_')
    chat_id = ids[0]
    message_id = ids[1]
    if message.document:
        bot.send_document(chat_id, document=message.document.file_id, reply_to_message_id=message_id)
    elif message.photo:
        bot.send_photo(chat_id, photo=message.photo[0].file_id, reply_to_message_id=message_id)
    else:
        bot.send_message(chat_id, text=text, reply_to_message_id=message_id)


@bot.message_handler(content_types=['text', 'document', 'photo'],
                     func=lambda message: str(message.chat.id) != config.TELEGRAM_MAIN_CHAT_ID)
def handle_document(message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    if message.document:
        message_data = message.document.file_id
        message_type = 'document'
    elif message.photo:
        message_data = message.photo[0].file_id
        message_type = 'photo'
    else:
        message_data = message.text
        message_type = 'text'

    user_id = str(message.from_user.id)
    if users.get(user_id):
        users[user_id].append({
            'message_id': message.id,
            'message_data': message_data,
            'message_type': message_type
        })
    else:
        users[user_id] = [{
            'message_id': message.id,
            'message_data': message_data,
            'message_type': message_type
        }]

    buttons = [
        types.InlineKeyboardButton(text, callback_data=str(index))
        for index, text in enumerate(document_types)
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id,
                     text='Выберите тип документа:',
                     reply_to_message_id=message.id,
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    bot.edit_message_text('Отправлено', call.message.chat.id, call.message.id)

    document_type = int(call.data)

    user_id = str(call.from_user.id)

    data = users[user_id].pop(0)
    message_id = data.get('message_id')
    message_data = data.get('message_data')
    message_type = data.get('message_type')

    user = call.from_user
    message = f'ID: {call.message.chat.id}_{message_id}\n' + \
              f'ФИО: {user.first_name} {user.last_name}\n' + \
              f'Тип Документа: {document_types[document_type]}'
    if message_type == 'document':
        bot.send_document(config.TELEGRAM_MAIN_CHAT_ID, document=message_data, caption=message)
    elif message_type == 'photo':
        bot.send_photo(config.TELEGRAM_MAIN_CHAT_ID, photo=message_data, caption=message)
    else:
        bot.send_message(config.TELEGRAM_MAIN_CHAT_ID, text=message + '\n\n' + message_data)


bot.polling()
