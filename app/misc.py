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
day_names_api_match = ("Понеділок", "Вівторок", "Середа", "Четвер", "П`ятниця", "Субота", "Неділя")
placeholders = ('ʘᴥʘ', '◕_◕', '⚆_⚆', '◔◡◔', '◠‿◠', 'U_U')

_day_names_ua = ("Понеділок", "Вівторок", "Середа", "Четвер", "П\'ятниця", "Субота", "Неділя")
_day_names_ru = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
_day_names_en = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_days_short_ua = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд')
_days_short_ru = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс')
_days_short_en = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
_week_name_ua = 'Тиждень'
_week_name_ru = 'Неделя'
_week_name_en = 'Week'
_sem_name_ua = 'Семестр'
_sem_name_ru = 'Семестр'
_sem_name_en = 'Semester'
day_names = {
    'ua': _day_names_ua,
    'ru': _day_names_ru,
    'en': _day_names_en
}
day_short_names = {
    'ua': _days_short_ua,
    'ru': _days_short_ru,
    'en': _days_short_en
}
week_name = {
    'ua': _week_name_ua,
    'ru': _week_name_ru,
    'en': _week_name_en
}
sem_name = {
    'ua': _sem_name_ua,
    'ru': _sem_name_ru,
    'en': _sem_name_en
}

helper_ua = "*Для студентів університету розроблені персональні електронні* [кабінети](https://studcabinet.kpi.kharkov.ua) *та* [Telegram бот](https://t.me/StudCabinet_Bot)*, " \
            "які є новим форматом залікових книжок.*\n\n" \
            "*В електронному кабінеті доступні такі сервіси:*\n" \
            "— Загальна інформація про студента\n" \
            "— Дані електронної залікової книжки\n" \
            "— Рейтинг студентів за результатами сесії (для призначення стипендії)\n" \
            "— Стан академічної заборгованості за попередній період\n" \
            "— Розклад роботи всіх спортивних секцій\n" \
            "— Навчальний план (по семестрах)\n" \
            "— Всі дані про оплату навчання (для контрактників)\n\n" \
            "Також передбачена можливість завантаження в кабінет електронної версії індивідуальної семестрової відомості з подальшою її роздруківкою (за бажанням студента), " \
            "а також, в перспективі, і інших довідок, які видаються деканатами.\n\n" \
            "Інші сервіси в даний час позначені в кабінеті, як неактивні. Усі вони будуть активуватися по мірі наповнення бази автоматизованої системи управління навчальним процесом. " \
            "Серед них — оголошення факультету (інституту, кафедри), графік ліквідації академічних заборгованостей студента, " \
            "новини прес-центру університету, розклад консультацій викладачів, обрання дисциплін вільного вибору, отримання переліку вакансій від Центру кар’єри. \n\n" \
            "Розробник нового сервісу — [Інформаційно-обчислювальний центр НТУ «ХПІ»](https://web.kpi.kharkov.ua/), " \
            "який діяв на підставі рішення [Вченої ради вишу](http://blogs.kpi.kharkov.ua/v2/vr/archives/1633?fbclid=IwAR2Gqbw_ACiCe2fQOCQBTaH9BnBn0uzPWlc9lPyCLa2qpfHSSed1rm44550) від 27 вересня 2019 р.\n\n" \
            "Для зворотнього зв\'язку натисніть \\[/feedback]"

helper_ru = "*Для студентов университета разработаны персональные электронные* [кабинеты](https://studcabinet.kpi.kharkov.ua) *и* [Telegram бот](https://t.me/StudCabinet_Bot)*, " \
            "которые являются новым форматом зачётных книжек.*\n\n" \
            "*В электронном кабинете доступны такие сервисы:*\n" \
            "— Общая информация про студента\n" \
            "— Данные электронной зачётной книжки\n" \
            "— Рейтинг студентов по результатам сессии (для назначения стипендии)\n" \
            "— Состояние академической задолженности за предыдущий период\n" \
            "— Расписание работы всех спортивных секций\n" \
            "— Учебный план (по семестрам)\n" \
            "— Все данные про оплату обучения (для контрактников)\n\n" \
            "Также предусмотрена возможность загрузки в кабинет электронной версии индивидуальной семестровой ведомости с дальнейшей её распечаткой (по желанию студента), " \
            "а также, в перспективе, и других справок, которые выдаются деканатами.\n\n" \
            "Другие сервисы на данный момент обозначены в кабинете, как неактивные. Все они будут активироваться по мере наполнения базы автоматизированной системы управления учебным процессом. " \
            "Среди них — объявления факультета (института, кафедры), график ликвидации академических задолженностей студента, " \
            "новости пресс-центра университета, расписание консультаций преподавателей, выбор дисциплин свободного выбора, получение списка вакансий от Центра карьеры. \n\n" \
            "Разработчик нового сервиса — [Информационно-вычислительный центр НТУ «ХПИ»](https://web.kpi.kharkov.ua/), " \
            "который действовал на основании решения [Учёного совета вуза](http://blogs.kpi.kharkov.ua/v2/vr/archives/1633?fbclid=IwAR2Gqbw_ACiCe2fQOCQBTaH9BnBn0uzPWlc9lPyCLa2qpfHSSed1rm44550) от 27 сентября 2019 г.\n\n" \
            "Для обратной связи нажмите \\[/feedback]"

helper_en = "*Personal* [e-cabinets](https://studcabinet.kpi.kharkov.ua) *and* [Telegram bot](https://t.me/StudCabinet_Bot) *have been developed for university students, " \
            "which are the new format of grade books.*\n\n" \
            "*Such services are available in the e-account:*\n" \
            "— General information about the student\n" \
            "— Electronic record book data\n" \
            "— Rating of students according to the results of the session (for the appointment of a scholarship)\n" \
            "— State of academic debt for the previous period\n" \
            "— Working hours of all sports sections\n" \
            "— Curriculum (by semester)\n" \
            "— All data about tuition fees (for contractors)\n\n" \
            "It is also possible to upload an electronic version of an individual semester report to the office with its further printout (at the request of the student), " \
            "as well as, in perspective, other certificates issued by deans.\n\n" \
            "Other services are currently indicated in the account as inactive. All of them will be activated as the base of the automated educational process management system is filled. " \
            "Among them are the announcements of the faculty (institute, department), the schedule for the elimination of the student's academic debts, " \
            "news of the university press center, schedule of teachers' consultations, choice of disciplines of free choice, receiving a list of vacancies from the Career Center. \n\n" \
            "New service developer — [Information and Computing Center NTU «KhPI»](https://web.kpi.kharkov.ua/), " \
            "which acted on the basis of the decision of the [Academic Council of the university](http://blogs.kpi.kharkov.ua/v2/vr/archives/1633?fbclid=IwAR2Gqbw_ACiCe2fQOCQBTaH9BnBn0uzPWlc9lPyCLa2qpfHSSed1rm44550) dated September 27, 2019 No.\n\n" \
            "For feedback click \\[/feedback]"
