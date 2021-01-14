import requests


async def delete_message(func, utils, **kwargs):
    try:
        await func(**kwargs)
    except utils.exceptions.MessageCantBeDeleted: pass
    except utils.exceptions.MessageToDeleteNotFound: pass


async def send_message(func, utils, **kwargs):
    try:
        await func(**kwargs)
    except utils.exceptions.BotBlocked: return
    except utils.exceptions.UserDeactivated: return
    except utils.exceptions.ChatNotFound: return
    except utils.exceptions.BadRequest: return
    return True


def req_post(url):
    try:
        response = requests.post(url)
    except requests.exceptions.ConnectionError:
        return
    return response

