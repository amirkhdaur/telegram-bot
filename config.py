from environs import Env

env = Env()
env.read_env()

TELEGRAM_TOKEN = env('TELEGRAM_TOKEN')
TELEGRAM_MAIN_CHAT_ID = env('TELEGRAM_MAIN_CHAT_ID')
