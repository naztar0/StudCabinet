import secrets
from sys import argv
from envparse import env
from dotenv import load_dotenv

load_dotenv()
DEBUG = False if len(argv) > 1 and argv[1] == '-O' else True

TG_TOKEN = env.str('TG_TOKEN')
WEBAPP_HOST = env.str('WEBAPP_HOST', default='0.0.0.0')
WEBAPP_PORT = env.int('WEBAPP_PORT', default=8080)

SECRET_KEY = "54ijzz8"
WEBHOOK_DOMAIN = env.str('WEBHOOK_DOMAIN', default='example.com')
WEBHOOK_BASE_PATH = env.str('WEBHOOK_BASE_PATH', default="/webhook")
WEBHOOK_PATH = f'{WEBHOOK_BASE_PATH}/{SECRET_KEY}'
WEBHOOK_URL = f'https://{WEBHOOK_DOMAIN}{WEBHOOK_PATH}'
WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.key'

MYSQL_HOST = env.str('MYSQL_HOST', default='localhost')
MYSQL_PORT = env.int('MYSQL_PORT', default=3306)
MYSQL_PASSWORD = env.str('MYSQL_PASSWORD', default='')
MYSQL_USER = env.str('MYSQL_USER', default='')
MYSQL_DB = env.str('MYSQL_DB', default='')

BOT_ADMIN = env.int('BOT_ADMIN', default=0)
