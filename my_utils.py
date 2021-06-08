import requests


async def delete_message(func, utils, **kwargs):
    try:
        await func(**kwargs)
    except utils.exceptions.MessageCantBeDeleted: pass
    except utils.exceptions.MessageToDeleteNotFound: pass


async def send_message(func, utils, **kwargs):
    try:
        return await func(**kwargs)
    except utils.exceptions.BotBlocked: return
    except utils.exceptions.UserDeactivated: return
    except utils.exceptions.ChatNotFound: return
    except utils.exceptions.BadRequest: return


def req_post(url):
    try:
        response = requests.post(url, timeout=20)
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        return
    return response


class ResTypes:
    MAIL = 0x00
    PASS = 0x01
    STUD_ID = 0x02
    LANG = 0x03
    GROUP_ID = 0x04
