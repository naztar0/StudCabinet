#!/usr/bin/env python
import os
from asyncio import get_event_loop, gather
from app import bot, config
from app.utils import updaters


def debug_check():
    if config.DEBUG:
        bot.start_pooling()
        exit()


def nt_main():
    loop = get_event_loop()
    for x in updaters.__all__:
        loop.create_task(x())
    # bot.start_webhook()  # TODO: not working
    bot.start_pooling()


def posix_main():
    if os.fork() == 0:
        # bot.start_webhook()  # TODO: not working
        bot.start_pooling()
        exit()
    if os.fork() == 0:
        loop = get_event_loop()
        loop.run_until_complete(gather(*(x() for x in updaters.__all__)))
        exit()


if __name__ == '__main__':
    debug_check()
    if os.name == 'nt':
        nt_main()
    elif os.name == 'posix':
        posix_main()
