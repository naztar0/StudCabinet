import logging
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from app import config


app_dir: Path = Path(__file__).parent.parent
locales_dir = app_dir / "locales"
temp_dir = app_dir / "temp"

logging.basicConfig(level=logging.WARNING)
i18n = I18nMiddleware('bot', locales_dir, default='ua')

bot = Bot(config.TG_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
dp.middleware.setup(i18n)
__ = i18n.gettext


api_url = "http://schedule.kpi.kharkov.ua/json"
api_cab = api_url + "/kabinet"
api_sport = api_url + "/sport"
api_sched = api_url + "/Schedule"
api_doc = api_url + "/getpdf"

qr_scan_url = 'https://27e1-93-178-222-144.eu.ngrok.io'


buttons_ua_1 = ("ℹ Загальна інформація", "📕 Залікова книжка", "📊 Рейтинг", "⚠ Борги", "📆 Розклад занять", "📆 Розклад спорт. каф.", "🗓 Навчальний план", "➡ Далі")
buttons_ru_1 = ("ℹ Общая информация", "📕 Зачётная книжка", "📊 Рейтинг", "⚠ Долги", "📆 Расписание занятий", "📆 Расписание спорт. каф.", "🗓 Учебный план", "➡ Дальше")
buttons_en_1 = ("ℹ General info", "📕 Record book", "📊 Rating", "⚠ Debts", "📆 Class schedule", "📆 Sport schedule", "🗓 Syllabus", "➡ Next")
buttons_ua_2 = ("💳 Оплати за навчання", "📄 Семестровий план", "🔍 Пошук студентів", "📨 Новини кафедри", "❓Підтримка", "🇺🇦 Мова", "⬅ Назад")
buttons_ru_2 = ("💳 Оплаты за обучение", "📄 Семестровый план", "🔍 Поиск студентов", "📨 Новости кафедры", "❓Помощь", "🐷 Язык", "⬅ Назад­")
buttons_en_2 = ("💳 Tuition fees", "📄 Semester plan", "🔍 Student search", "📨 Cathedra news", "❓Help", "🇬🇧 Language", "⬅ Back")
sign_in_butt = "👥 Увійти в кабінет"
req_err_msg = "😔 Не вдалося виконати запит, спробуйте пізніше"
auth_err_msg = "Помилка аутентифікації, повторіть спробу входу"
greetings_text = "*Введіть email і пароль від особистого кабінету*\n\nНаприклад:\ndemo@gmail.com d2v8F3"
faculties = ('КІТ', 'КН', 'СГТ', 'БЕМ', 'Е')
para_num = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣')
para_name = ('Para1', 'Para2', 'Para3', 'Para4', 'Para5', 'Para6')
day_names_api_match = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П`ятниця', 'Субота', 'Неділя')
days_names = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
days_short = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
placeholders = ('ʘᴥʘ', '◕_◕', '⚆_⚆', '◔◡◔', '◠‿◠', 'U_U')
