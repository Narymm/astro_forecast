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
logging.disable(logging.CRITICAL)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена из переменных окружения
bot_token = os.getenv('BOT_TOKEN')

# Определение состояний для ConversationHandler
ASK_NAME, QUESTION1, QUESTION2, QUESTION3, GET_DATA, RESULT = range(6)

# Вопросы и варианты ответов
questions = [
    "Выберите ваш знак зодиака",
    "Как прошел август для вас?",
    "Если вам интересно узнать <b>индивидуальный прогноз-тенденции месяца по вашей натальной карте рождения</b> БЕСПЛАТНО 🎁, оставьте ваши данные: <i>дата, время и город рождения</i>.\nИ я вам пришлю ответ в личные сообщения."
    
]
options = [
    ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    ["Удачно", "Сложно"],
    ["Отправить данные", "Нет, спасибо"]
]

# Описание результатов на основе ответов

results = {
    "Овен": {
        "description": "<i><u>ОВЕН</u></i>\n\nЦелый месяц происходят трансформации в работе, всё меняется или резко рушится. Нужно принять эти изменения. Пересмотреть, улучшить, отбросить старое и отжившее. с 1 по 4 сентября будет много встреч и переговоров, но они не всегда будут идти легко. С 5 сентября вас будут волновать вопросы семьи и недвижимости:где жить, с кем, и как это всё организовать. С середины месяца будьте внимательны к своему здоровью, могут всплыть старые болячки или их первопричины. Запрятанные глубинные эмоции тяжело будет удержать в себе. Поберегите нервную систему. На протяжении всего месяца вам неожиданно нужно будет решать какие-либо финансовые вопросы, например, возвращать долг, который может прилететь из прошлого.",
        "image": os.getenv('OVEN')
    },
    "Телец": {
        "description": "<i><u>ТЕЛЕЦ</u></i>\n\nНа протяжении месяца вас ожидают трансформации, связанные с дальними путешествиями и за границей. Возможно, вы поймете, что привычные ценности утратили актуальность и больше не будет как прежде. Вплоть до 22 сентября вам будут важны вопросы здоровья и работы. Есть шанс удачно всё разрешить. А в конце месяца могут разыграться нешуточные “страсти” с партнерами, захочется больше внимания, любви и денег от них. С середины месяца помотают нервы романтические отношения или ваши друзья, будет тяжело найти общий язык. Вам покажется, что к вам слишком строги и требовательны.\nЦелый месяц вам захочется резко изменить что-то в своей внешности, вернуть что-то из прошлого. Возможно, вам удастся по-новому взглянуть на себя, используя старые “приёмы”.",
        "image": os.getenv('TELEC')
    },
    "Близнецы": {
        "description": "<i><u>БЛИЗНЕЦЫ</u></i>\n\nМесяц для вас может оказаться Перерождением. Возможные кризисы могут вас вывести на новый уровень. Или принести финансовые вести. С 1 по 8 сентября - время встреч, переговоров, поездок и обучений. Нужно воспользоваться моментом и извлечь для себя пользу. С 9 по 25 сентября - вас будет интересовать вопросы недвижимости и семьи, хорошее время для таких дел. С 26 сентября - тема детей, личных отношений может вас захлестнуть с головой. С середины месяца сложно будет найти баланс между домом и работой. Будет складываться ощущение, что в семье вы не можете забыть о работе, а на работе будете решать домашние дела. В сентябре неожиданно придут новости из прошлого, возможно, партнёры, которые наведут шороху в вашей жизни. Есть шанс взглянуть на человека новыми глазами.",
        "image": os.getenv('BLIZNECU')
    },
    "Рак": {
        "description": "<i><u>РАК</u></i>\n\nВ сентябре можете отблагодарить ваших партнеров и оппонентов за кризисы и трансформации. Возможно, кто-то изменит вашу жизнь, и не всегда положительно, будьте бдительны. До 22 сентября у вас будет возможность наладить контакты, и отправиться в полезное путешествие или на обучение. В конце месяца - для вас будут актуальны вопросы семьи и дома. С Середины сентября будьте внимательны при заключении сделок и договоров, есть шанс просчитаться. Или на эмоциях сделать неверный выбор. Целый месяц друзья из прошлого могут напоминать о себе, возможно, сможете реализовать удачный проект, который долго пылился на полке.",
        "image": os.getenv('RAK')
    },
    "Лев": {
        "description": "<i><u>ЛЕВ</u></i>\n\nВ сентябре будьте внимательны со здоровьем, могут быть кризисные ситуации. Не перерабатывайте, не берите на себя больше, чем можете взять. Вопросы со здоровьем из прошлого, а также старая работа могут напомнить о себе. До 22 сентября для вас будут актуальны вопросы финансов и ресурсности, как материальной, так и физической. Отличное время, чтобы заняться этими вопросами. С середины месяца могут быть эмоциональные вопросы связанные с вашими и чужими деньгами. Вспомните, никому не задолжали, или вам. Данный вопрос, в это время, может сильно задеть. Целый месяц темы работы не будут вас покидать. Может появиться неожиданно проект из прошлого, или возможность вернуться к важным рабочим обязанностям. Благодаря этому сможете вырасти в карьере.",
        "image": os.getenv('LEV')
    },
    "Дева": {
        "description": "<i><u>ДЕВА</u></i>\n\nСентябрь - ваш месяц, чтобы заявить о себе и изменить в жизни то, что не устраивает. Обновить свои важные сферы. До середины месяца будет больше возможностей. Вас ожидают трансформации в личной жизни, перемены в детской теме и творчестве. С середины сентября для вас откроются новые “тайны” о близких людях и вашем окружении. Не вся информация будет положительной, не стоит питать иллюзий. Особенно это коснётся Дев, что родились с 15 по 21 сентября. С 26 сентября будут волновать вопросы финансов. Весь месяц вас неожиданно могут возвращать прошлые вопросы, связанные с дальней поездкой и заграницей. Возможно, вы смените ваши ориентиры и ценности, пересмотрите приоритеты в жизни.",
        "image": os.getenv('DEVA')
    },
    "Весы": {
        "description": "<i><u>ВЕСЫ</u></i>\n\nВесь месяц вы будете возвращаться к вопросам семьи и недвижимости, где жить, как организовать быт. Эту сферу ожидают трансформации, вполне возможно, что вы переедете на новое место. До 22 сентября будет легче решить личные вопросы, также вы задумаетесь о смене имиджа. Отличное время, чтобы заявить о себе. С середины месяца вас могут эмоционально задеть вопросы, связанные с работой, это может коснуться и здоровья. Поберегите себя. Весь месяц могут быть неожиданные стрессы и кризисы, особенно, связанные с вашими накоплениями и финансами. Будьте внимательны с этой сферой.",
        "image": os.getenv('VESU')
    },
    "Скорпион": {
        "description": "<i><u>СКОРПИОН</u></i>\n\nВесь месяц вас ожидают перемены в сфере коммуникаций и обучения. Произойдет смена окружения, вашего круга общения. Также произойдут долгожданные изменения у ваших родственников - братьев и сестер. Вполне возможно, что вас ожидает много поездок, а также возможность овладеть новыми навыками и знаниями, что укрепит ваши позиции в вашей деятельности. С 5 сентября ваш фокус внимания будет устремлён на иностранную сферу. Возможно начнете изучать иностранный язык или решите работать на границей. Произойдет расширение горизонтов. С середины месяца могут задевать вопросы в личной сфере и вопросы с детьми. Непросто будет разрешить какие-то вопросы и найти общий язык. С 23 сентября у вас появится возможность заявить о себе, ведь вы будете привлекать взгляды. Ваши обаяние и харизма помогут в реализации задуманного. Неожиданные изменения коснутся ваших партнёров, вы по-новому взгляните на людей.",
        "image": os.getenv('SKORPION')
    },
    "Стрелец": {
        "description": "<i><u>СТРЕЛЕЦ</u></i>\n\nВесь месяц будут происходить изменения в финансовой сфере. Могут быть как и потери, так и положительные трансформации. В любом случае будьте внимательными к этой теме, чтобы не потерять свои сбережения. В этом месяце, как никогда, для вас будут актуальны личные и партнерские бизнес-отношения. С середины месяца вас будут волновать жилищный вопрос, семья и родители. Есть риск столкнуться с иллюзиями и внешним сопротивлением. Может быть не просто. В сентябре могут произойти резкие изменения в работе, возможно, к вам вернуться прошлые проекты, либо старые коллеги предложат новую работу.",
        "image": os.getenv('STRELEC')
    },
    "Козерог": {
        "description": "<i><u>КОЗЕРОГ</u></i>\n\nВас ожидает месяц трансформаций, которые коснутся именно вас, вашего тела, имиджа, позиционирования. Нужно быть готовым, что не всегда перемены будут положительными. Возможно, это то самое время, когда нужно будет отпустить старое. И начать с самого начала. Весь месяц можете решать много вопросов с документами, поездками и коммуникациями. Не всегда будет всё будет идти гладко. Особенно с середины месяца данные сферы вас заставят понервничать. Возможны недопонимания, ошибки и накладки. Всё тщательно перепроверяйте. Весь сентябрь возможны резкие изменения в любовной сфере, также в теме детей, творческих проектов. Вернетесь к прошлым вопросам, что теперь уж точно нельзя будет отложить на потом.",
        "image": os.getenv('KOZEROG')
    },
    "Водолей": {
        "description": "<i><u>ВОДОЛЕЙ</u></i>\n\nВесь сентябрь удачно посвятить время вашим глубинным трансформациям. Особенно, если вы давно мечтали изучить и погрузиться в недоступные для всех темы. Перемены могут коснуться и вашего прошлого, то, что вы никак не могли ожидать. Резкие изменения затронут семью, родителей или тему недвижимости. Возможно, вы снова переедете или решите вернуться в старое место. С середины сентября финансовая сфера заставит понервничать. Возможны разочарования и обманы. Будьте бдительны, особенно с 15 по 22 сентября.",
        "image": os.getenv('VODOLEJ')
    },
    "Рыбы": {
        "description": "<i><u>РЫБЫ</u></i>\n\nВесь месяц ожидайте трансформаций в своих проектах. Друзья из прошлого могут внести изменения в вашу жизнь. Иногда стоит не сопротивляться, даже, если вас могут ожидать потери и разочарования. Воспринимайте месяц как возможность перемен. Всё к лучшему. В сентябре будут особенно актуальны темы, связанные с вашей внешностью, имиджем и позиционированием. Хорошее время, чтобы пересмотреть данные темы. С середины месяца могут эмоционально задевать вопросы, связанные с вашей личностью и с вашими партнёрами, как личные, так из рабочей среды. Есть риск недопониманий, излишних иллюзий. Стоит взять себя в руки, чтобы выдержать внешний поток сопротивления. Резкие изменения могут затронуть сферы коммуникаций, поездок и обучений.",
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
        reply_markup=create_inline_keyboard(options[0], row_width=3)  # Задаем 3 кнопки в ряду
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
            parse_mode='HTML'
        )
        return QUESTION1 + current_state
    
    elif current_state == len(questions) and query.data == "Отправить данные":
        if context.user_data['telegram_account'] == None:
             await query.message.reply_text(
                 'Пожалуйста, введите <b><i>Данные</i></b> и укажите <b><i>Контакт</i></b>, по которому можно с вами связаться (аккаунт ТГ/телефон/почта):',
                 parse_mode='HTML'
            )
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
                    caption=f'<b>Прогноз на сентябрь:</b>\n\n{description}',
                    parse_mode='HTML'
                )
        else:
            await query.message.reply_text(
                f'<b>Прогноз на сентябрь:</b>\n\n{result_description}',
                parse_mode='HTML'
            )

        write_to_google_sheets(context.user_data)
        context.user_data['answers'] = []
        await query.message.reply_text('Присоединяйтесь к моему <a href="https://t.me/astro_nataly_bonum">ТГ-каналу</a> и <a href="https://www.instagram.com/nataly_bonum?igsh=MWo5emFvczUwaHUyNQ==">Инстаграмм</a>, где я делюсь астро-тенденциями и своей жизнью.\nА также, познакомьтесь с моим <a href="https://astronbonum.tilda.ws">сайтом</a>.\n\n❤️ Буду ждать вас там!\n\nДо встречи!',
                                       parse_mode='HTML'
                                       )
        return ConversationHandler.END
    
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
                caption=f'<b>Прогноз на сентябрь:</b>\n\n{description}',
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            f'<b>Прогноз на сентябрь:</b>\n\n{result_description}',
            parse_mode='HTML'
        )
    
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
