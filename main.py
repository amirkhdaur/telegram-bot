import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TELEGRAM_TOKEN, parse_mode='HTML')

bot_info = bot.get_me()
bot_id = bot_info.id

document_types = [
    'счет к оплате',
    'акт выполненных работ/ накладная на товар от продавца',
    'акт выполненных работ/ накладная на товар для покупателя',
    'доверенность на получение товара',
    'акт сверки',
    'прочее'
]


@bot.message_handler(commands=['getchatid'])
def get_chat_id(message):
    bot.reply_to(message, message.chat.id)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Отправьте текст, фото или файл')


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


@bot.message_handler(content_types=['text', 'document', 'photo'],
                     func=lambda message: str(message.chat.id) != config.TELEGRAM_MAIN_CHAT_ID)
def handle_document(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
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

    message = call.message.reply_to_message
    user = call.from_user
    text = f'ID: {call.message.chat.id}_{message.id}\n' + \
           f'Имя: {user.first_name} {user.last_name}\n' + \
           f'Тип Документа: <b>{document_types[document_type]}</b>'

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
