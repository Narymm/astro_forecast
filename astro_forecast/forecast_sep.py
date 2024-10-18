import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, MessageHandler, filters, ApplicationBuilder, Updater, JobQueue, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# Выключаем логирование
#logging.disable(logging.CRITICAL)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена из переменных окружения
bot_token = os.getenv('BOT_TOKEN')

# Определение состояний для ConversationHandler
ASK_NAME, QUESTION1, QUESTION2, QUESTION3, GET_DATA, RESULT, GET_FIRST_ANSWER = range(7)

# Описание результатов на основе ответов

results = {
    "Овен": {
        "image": os.getenv('OVEN')
    },
    "Телец": {
        "image": os.getenv('TELEC')
    },
    "Близнецы": {
        "image": os.getenv('BLIZNECU')
    },
    "Рак": {
        "image": os.getenv('RAK')
    },
    "Лев": {
        "image": os.getenv('LEV')
    },
    "Дева": {
        "image": os.getenv('DEVA')
    },
    "Весы": {
        "image": os.getenv('VESU')
    },
    "Скорпион": {
        "image": os.getenv('SKORPION')
    },
    "Стрелец": {
        "image": os.getenv('STRELEC')
    },
    "Козерог": {
        "image": os.getenv('KOZEROG')
    },
    "Водолей": {
        "image": os.getenv('VODOLEJ')
    },
    "Рыбы": {
        "image": os.getenv('RUBU')
    },
}

# Путь к локальному изображению для приветственного сообщения
#WELCOME_PHOTO_PATH = 'C:/Users/narym/Chatbots/test/test/IMG_0969.jpg'  # Замените на путь к вашему изображению
WELCOME_PHOTO_PATH = os.getenv('WELCOME_PHOTO_PATH')

# Функция для генерации inline клавиатуры
def create_inline_keyboard(options, row_width=2):
    keyboard = []
    for i in range(0, len(options), row_width):
        keyboard.append([InlineKeyboardButton(option, callback_data=option) for option in options[i:i+row_width]])
    return InlineKeyboardMarkup(keyboard)

# Функция для генерации стартовой inline клавиатуры
def start_keyboard():
    keyboard = [[InlineKeyboardButton("Прогноз на сентябрь", callback_data="start_survey")]]
    return InlineKeyboardMarkup(keyboard)

# Настройка доступа к Google Sheets
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv('GOOGLE_CREDENTIALS_PATH'), scope)
    client = gspread.authorize(creds)
    return client

# Подключение к Google Sheets API
def get_google_sheet(table_name, sheet_name):
    client = get_gspread_client()
    sheet1 = client.open(table_name).worksheet(sheet_name)  # Замените на имя вашего листа
    
    # Получаем все данные из листа
    data = sheet1.get_all_records()
    return data

# Получение данных из Google Таблицы
table_name = 'ChatBotBD'  # имя таблицы Google
sheet_name1 = 'Questions_Answers'  # Название листа
sheet_name2 = 'Results'

data1 = get_google_sheet(table_name, sheet_name1)
data2 = get_google_sheet(table_name, sheet_name2)

# Преобразуем данные в вопросы, варианты и результаты
questions = [row['Вопросы'] for row in data1]
options = [row['Варианты'].split("|") for row in data1]
#results = {row['Результат']: {'description': row['Описание'], 'image': row['Картинка']} for row in data}
description = {row['Результат']: {'description': row['Описание']} for row in data2}

for key in results:
    if key in description:
        results[key]['description'] = description[key]['description']

# Запись данных в Google Sheets
def write_to_google_sheets(user_data):
    client = get_gspread_client()
    sheet = client.open("ChatBotBD").worksheet("Forecast_sep")  # Замените на имя вашего листа

    # Подготовка данных для записи
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_data['username'], user_data['telegram_account'], user_data['id']] + user_data['answers'] + [user_data.get('addit_data', '')]
    sheet.append_row(row)

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> int:
    with open(WELCOME_PHOTO_PATH, 'rb') as photo:
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo,
            caption='<b>ПРОГНОЗ на СЕНТЯБРЬ для вашего ЗНАКА ЗОДИАКА</b> 👇🏼\n\nНас ожидает месяц проявленности и возможности закрепить свои позиции. Сентябрь может быть плодотворным, особенно, если вы позаботились об этом еще в июле и в августе.\n\nУзнайте, что вам принесёт <b>СЕНТЯБРЬ</b> ▶️\n\n<b>+ Подарок</b> 💝\n\n✅ <b>Определю индивидуальные тенденции месяца</b> эксклюзивно для вас\n\nУзнать прогноз на СЕНТЯБРЬ 👇🏼',
            parse_mode='HTML',
            reply_markup=start_keyboard()
        )
    return ASK_NAME

# Функция для обработки начала опроса
async def start_survey(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text('Пожалуйста, введите ваше имя:')
    return ASK_NAME

# Функция для обработки имени пользователя
async def ask_name(update: Update, context: CallbackContext) -> None:
    context.user_data['username'] = update.message.text
    context.user_data['telegram_account'] = update.message.from_user.username  # Сохраняем аккаунт Telegram
    context.user_data['id'] = update.message.from_user.id  # Сохраняем id Telegram
    await update.message.reply_text(
        questions[0],
        reply_markup=create_inline_keyboard(options[0], row_width=3),  # Задаем 3 кнопки в ряду
        parse_mode='Markdown'
    )
    return QUESTION1

# Функция для обработки завершения опроса и отправки результата

# Функция для обработки ответов на вопросы
async def handle_question(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    answers = context.user_data.setdefault('answers', [])
    answers.append(query.data)
    
    current_state = len(answers)
    
    if current_state < len(questions):  # Учитываем, что последний вопрос - это вопрос о данных
        await query.message.reply_text(
            questions[current_state],
            reply_markup=create_inline_keyboard(options[current_state]),
            parse_mode='Markdown'
        )
        return QUESTION1 + current_state
    
    elif current_state == len(questions) and query.data == "Отправить данные":
        if context.user_data['telegram_account'] is None:
             await query.message.reply_text(
                 '<b>Возможно, ваш личный контакт скрыт. Если вы хотели бы получить разбор, то укажите ваш <u>аккаунт через @ или номер телефона</u>, привязанный к этому аккаунту.</b>',
                 parse_mode='HTML'
             )
             return GET_FIRST_ANSWER
        else:
            await query.message.reply_text(
                'Пожалуйста, введите данные:'
            )
        return GET_DATA

    else:
        first_answer = answers[0]
        result_description = results.get(first_answer, "Ваши ответы уникальны, и мы не можем дать конкретное описание.")
        
        if result_description:
            description = result_description['description']
            image_path = result_description['image']
        
            # Отправляем изображение
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=description,
                    parse_mode='Markdown'
                )
        else:
            await query.message.reply_text(result_description, parse_mode='Markdown')

        write_to_google_sheets(context.user_data)
        context.user_data['answers'] = []
        await query.message.reply_text('Присоединяйтесь к моему <a href="https://t.me/astro_nataly_bonum">ТГ-каналу</a> и <a href="https://www.instagram.com/nataly_bonum?igsh=MWo5emFvczUwaHUyNQ==">Инстаграмм</a>, где я делюсь астро-тенденциями и своей жизнью.\nА также, познакомьтесь с моим <a href="https://astronbonum.tilda.ws">сайтом</a>.\n\n❤️ Буду ждать вас там!\n\nДо встречи!',
                                       parse_mode='HTML'
                                       )
        return ConversationHandler.END

async def get_first_answer(update: Update, context: CallbackContext) -> int:
    # Получаем ответ пользователя на первый вопрос
    user_answer = update.message.text
    context.user_data['telegram_account'] = user_answer  # Сохраняем ответ в user_data
    
    await update.message.reply_text(
        'Пожалуйста, введите данные: <b>дата, время и город рождения</b>',
        parse_mode='HTML'
    )
    return GET_DATA

# Функция для обработки данных
async def get_addit_data(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    context.user_data['addit_data'] = user_input
    
    first_answer = context.user_data['answers'][0]
    result_description = results.get(first_answer, "Ваши ответы уникальны, и мы не можем дать конкретное описание.")
    
    if result_description:
        description = result_description['description']
        image_path = result_description['image']
        
        # Отправляем изображение
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=photo,
                caption=description,
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(result_description, parse_mode='Markdown')
    
    write_to_google_sheets(context.user_data)
    context.user_data['answers'] = []
    await update.message.reply_text('<i>В ближайшее время я свяжусь с вами ❤️\nИ предоставлю <b>ИНДИВИДУАЛЬНЫЕ</b> тенденции сентября по вашей натальной карте ☀️\nЧто поможет вам <b>расставить СВОИ ориентиры</b> в этот период</i>\n\nА пока, вы можете присоединиться к моему <a href="https://t.me/astro_nataly_bonum">ТГ-каналу</a> и <a href="https://www.instagram.com/nataly_bonum?igsh=MWo5emFvczUwaHUyNQ==">Инстаграмм</a>, где я делюсь астро-тенденциями и своей жизнью.\nА также, познакомиться с моим <a href="https://astronbonum.tilda.ws">сайтом</a>.\n\nДо связи!', 
                                    parse_mode='HTML'
                                    )
    return ConversationHandler.END

# Функция для обработки отмены опроса
async def cancel(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        'Опрос прерван.'
    )
    return ConversationHandler.END

# Обработчик ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f'Update {update} caused error {context.error}')

async def send_ping(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.send_message(chat_id="504662108", text="Ping!")

def main() -> None:
    application = ApplicationBuilder().token(bot_token).build()

    # Получаем JobQueue
    job_queue = application.job_queue

    if job_queue is None:
        print("JobQueue не инициализирован!")
        return

    job_queue.run_repeating(send_ping, interval=timedelta(minutes=60), first=timedelta(seconds=10), name="ping_job", data="chat_id")


    # Определение обработчика разговора с состояниями
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern='start_survey')],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            QUESTION1: [CallbackQueryHandler(handle_question, pattern='^(Овен|Телец|Близнецы|Рак|Лев|Дева|Весы|Скорпион|Стрелец|Козерог|Водолей|Рыбы)$')],
            QUESTION2: [CallbackQueryHandler(handle_question, pattern='^(Удачно|Сложно)$')],
            QUESTION3: [CallbackQueryHandler(handle_question, pattern='^(Отправить данные|Нет, спасибо)$')],
            GET_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_addit_data)],
            GET_FIRST_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_answer)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))  # Обработка текстовых сообщений
    application.add_error_handler(error_handler)

    application.run_polling()
 
if __name__ == '__main__':
    main()
