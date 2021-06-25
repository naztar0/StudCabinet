import requests


class ResTypes:
    MAIL = 0x00
    PASS = 0x01
    STUD_ID = 0x02
    LANG = 0x03
    GROUP_ID = 0x04
    FACULTY = 0x05


class Keyboards:
    UA_1 = 0x00
    UA_2 = 0x01
    RU_1 = 0x02
    RU_2 = 0x03


class CallbackFuncs:
    PAGE_1 = 0x00
    PAGE_2 = 0x01
    PAGE_3 = 0x02
    PAGE_4 = 0x03
    PAGE_5 = 0x04
    SCHEDULE = 0x05
    SPORT_TYPE = 0x06
    SPORT_DAY = 0x07
    RATING_SHOW_ALL = 0x08
    RATING_SHOW_ALL_SORT = 0x09
    HISTOGRAM_2 = 0x0a
    HISTOGRAM_4 = 0x0b


async def delete_message(func, exceptions, **kwargs):
    try:
        await func(**kwargs)
    except (exceptions.MessageCantBeDeleted,
            exceptions.MessageToDeleteNotFound): pass


async def send_message(func, exceptions, **kwargs):
    try:
        return await func(**kwargs)
    except (exceptions.BotBlocked,
            exceptions.UserDeactivated,
            exceptions.ChatNotFound,
            exceptions.BadRequest): return


def req_post(url, method='POST'):
    try:
        if method == 'POST':
            response = requests.post(url, timeout=20)
        elif method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            return
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError): return
    return response


def esc_markdown(s):
    return s.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[')
